import abc
import logging
import weakref
from dataclasses import dataclass
from functools import partial
from typing import List

from hyperapp.client.commander import BoundCommand
from hyperapp.client.module import ClientModule

from . import htypes
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


@dataclass
class VisualItem:
    name: str
    text: str
    children: List['VisualItem'] = None
    commands: List[BoundCommand] = None

    def with_added_commands(self, commands_it):
        all_commands = [*self.commands, *commands_it]
        return VisualItem(self.name, self.text, self.children, all_commands)


class VisualItemDiff:
    pass


@dataclass
class InsertVisualItemDiff(VisualItemDiff):
    path: List[int]
    idx: int
    item: VisualItem


@dataclass
class RemoveVisualItemDiff(VisualItemDiff):
    path: List[int]


@dataclass
class UpdateVisualItemDiff(VisualItemDiff):
    path: List[int]
    item: VisualItem


class LayoutWatcher:

    def __init__(self):
        self._observers = weakref.WeakSet()

    def subscribe(self, observer):
        self._observers.add(observer)

    def distribute_diffs(self, diff_list):
        _log.info("Distribute layout diffs %s to %s", diff_list, list(self._observers))
        for observer in self._observers:
            observer.process_layout_diffs(diff_list)


class LayoutHandle(metaclass=abc.ABCMeta):

    def __init__(self, ref_registry, object_layout_association, layout, watcher):
        self._ref_registry = ref_registry
        self._object_layout_association = object_layout_association
        self._layout = layout
        self._watcher = watcher
        self._watcher.subscribe(self)

    @property
    def layout(self):
        return self._layout

    @property
    def watcher(self) -> LayoutWatcher:
        return self._watcher

    def command_handle(self):
        assert 0  # todo
        return CommandLayoutHandle(self._ref_registry, self._object_layout_association)

    async def set_layout(self, layout):
        self._layout = layout
        item = await layout.visual_item()
        self._watcher.distribute_diffs([UpdateVisualItemDiff(['root'], item)])

    @property
    @abc.abstractmethod
    def command_path(self):
        pass

    def process_layout_diffs(self, diff_list):
        _log.info("Save layout association for category %s/%s to %s", self._category, '/'.join(self._path), self._layout.data)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        self._object_layout_association[self._category] = layout_ref


class DefaultLayoutHandle(LayoutHandle):

    @classmethod
    async def from_data(
            cls, state,
            ref_registry, default_object_layouts, object_layout_association, object_layout_registry, object_type_resolver, layout_handle_cache,
            ):
        object_type = object_type_resolver.resolve_ref_to_object(state.object_type_ref)
        handle = await self.from_object_type(
            object_type, ref_registry, default_object_layouts, object_layout_association, object_layout_registry, object_type_resolver, layout_handle_cache)
        return handle

    @classmethod
    async def from_object_type(
            cls, object_type,
            ref_registry, default_object_layouts, object_layout_association, object_layout_registry, object_type_resolver, layout_handle_cache,
            ):
        try:
            return layout_handle_cache[object_type, ()]
        except KeyError:
            pass
        layout_ref = cls._resolve_association(object_layout_association, object_type)
        watcher = LayoutWatcher()
        if layout_ref:
            layout = await object_layout_resolver.resolve_async(layout_ref, ['root'], object_type, watcher)
        else:
            layout = await default_object_layouts.construct_default_layout(object_type, watcher, object_layout_registry)
        return cls(ref_registry, object_layout_association, layout, watcher, object_type)

    @staticmethod
    def _resolve_association(object_layout_association, object_type):
        object_type_t = object_type._t
        while object_type_t:
            try:
                return object_layout_association[object_type_t]
            except KeyError:
                object_type_t = object_type_t.base
        return None

    def __init__(self, ref_registry, object_layout_association, layout, watcher, object_type):
        super().__init__(ref_registry, object_layout_association, layout, watcher)
        self._object_type = object_type

    @property
    def title(self):
        return f"Layout for: {self._object_type._t.name}"

    @property
    def data(self):
        object_type_ref = self._ref_registry.register_object(self._object_type)
        return htypes.layout.default_layout_handle(object_type_ref)

    @property
    def command_path(self):
        return []


class CommandLayoutHandle(LayoutHandle):

    @classmethod
    async def from_data(cls, state, ref_registry, object_type_resolver, layout_handle_resolver, layout_handle_cache):
        base_handle = layout_handle_resolver.resolve(state.base_handle_ref)
        handle = await layout_handle_registry.produce_handle(object_type)
        return handle.with_path(state.path)

    def __init__(self, ref_registry, object_layout_association, layout, watcher, base, command_id):
        super().__init__(ref_registry, object_layout_association, layout, watcher)
        self._base = base
        self._command_id = command_id

    @property
    def title(self):
        return f"Layout for: {self._object_type._t.name}"

    @property
    def data(self):
        object_type_ref = self._ref_registry.register_object(self._object_type)
        return htypes.layout.default_layout_handle(object_type_ref)

    @property
    def command_path(self):
        return [*self._base.command_path, self.command_id]


class CommandLayoutHandle(LayoutHandle):

    @classmethod
    async def from_data(cls, state, layout_handle_registry):
        handle = await layout_handle_registry.produce_handle(object, category=state.category)
        return handle.with_path(state.path)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)

        services.layout_handle_cache = {}  # object_type, command path -> layout handle

        services.layout_handle_codereg = AsyncCapsuleRegistry('layout_handle', services.type_resolver)
        services.layout_handle_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.layout_handle_codereg)
        services.layout_handle_codereg.register_type(
            htypes.layout.default_layout_handle, DefaultLayoutHandle.from_data,
            services.ref_registry, services.object_layout_association, services.object_type_resolver, services.layout_handle_cache)

        self._ref_registry = services.ref_registry
        self._default_object_layouts = services.default_object_layouts
        self._object_layout_association = services.object_layout_association
        self._object_layout_registry = services.object_layout_registry
        self._object_type_resolver = services.object_type_resolver
        self._layout_handle_cache = services.layout_handle_cache

        services.layout_handle_from_object_type = self._layout_handle_from_object_type

    async def _layout_handle_from_object_type(self, object_type):
        handle = await DefaultLayoutHandle.from_object_type(
            object_type, self._ref_registry, self._default_object_layouts, self._object_layout_association,
            self._object_layout_registry, self._object_type_resolver, self._layout_handle_cache)
        return handle
