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
    current_commands: List[BoundCommand] = None
    all_commands: List[BoundCommand] = None

    def with_added_commands(self, commands_it):
        added_commands = list(commands_it)
        current_commands = [*self.current_commands, *added_commands]
        all_commands = [*self.all_commands, *added_commands]
        return VisualItem(self.name, self.text, self.children, current_commands, all_commands)


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

    def __init__(self, ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher):
        self._ref_registry = ref_registry
        self._object_layout_resolver = object_layout_resolver
        self._object_layout_association = object_layout_association
        self._layout_handle_cache = layout_handle_cache
        self._layout = layout
        self._watcher = watcher
        self._watcher.subscribe(self)

    @property
    def layout(self):
        return self._layout

    @property
    def watcher(self) -> LayoutWatcher:
        return self._watcher

    async def command_handle(self, command_id, layout_ref):
        async def handle_constructor():
            watcher = LayoutWatcher()
            layout = await self._object_layout_resolver.resolve(layout_ref, ['root'], watcher)
            return CommandLayoutHandle(self._ref_registry, self._object_layout_association, layout, watcher, command_id)
        command_path = [*self.command_path, command_id]
        return await self.with_layout_cache(self._layout_handle_cache, self.base_object_type, command_path, handle_constructor)

    async def set_layout(self, layout):
        self._layout = layout
        item = await layout.visual_item()
        self._watcher.distribute_diffs([UpdateVisualItemDiff(['root'], item)])

    @staticmethod
    async def with_layout_cache(layout_handle_cache, object_type, command_path, handle_constructor):
        command_path = tuple(command_path)
        try:
            return layout_handle_cache[object_type, command_path]
        except KeyError:
            pass
        handle = await handle_constructor()
        layout_handle_cache[object_type, command_path] = handle
        return handle

    @property
    @abc.abstractmethod
    def base_object_type(self):
        pass

    @property
    @abc.abstractmethod
    def command_path(self):
        pass


class DefaultLayoutHandle(LayoutHandle):

    @classmethod
    async def from_data(
            cls,
            state,
            ref_registry,
            async_ref_resolver,
            object_layout_resolver,
            object_layout_association,
            layout_handle_cache,
            layout_from_object_type,
            ):
        object_type = await async_ref_resolver.resolve_ref_to_object(state.object_type_ref)
        return (await cls.from_object_type(
            object_type,
            ref_registry,
            async_ref_resolver,
            object_layout_resolver,
            object_layout_association,
            layout_handle_cache,
            layout_from_object_type,
            ))

    @classmethod
    async def from_object_type(
            cls,
            object_type, 
            ref_registry,
            async_ref_resolver,
            object_layout_resolver,
            object_layout_association,
            layout_handle_cache,
            layout_from_object_type,
            ):
        async def handle_constructor():
            watcher = LayoutWatcher()
            layout = await layout_from_object_type(object_type, watcher)
            return cls(ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher, object_type)
        handle = await cls.with_layout_cache(layout_handle_cache, object_type, [], handle_constructor)
        return handle

    def __init__(self, ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher, object_type):
        super().__init__(ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher)
        self._object_type = object_type

    @property
    def title(self):
        return f"Layout for: {self._object_type._t.name}"

    @property
    def data(self):
        object_type_ref = self._ref_registry.register_object(self._object_type)
        return htypes.layout.default_layout_handle(object_type_ref)

    @property
    def base_object_type(self):
        return self._object_type

    @property
    def command_path(self):
        return []

    def process_layout_diffs(self, diff_list):
        _log.info("Save layout association for %r to %s", self._layout.object_type, self._layout.data)
        self._object_layout_association.associate(self._object_type, self._layout)


class CommandLayoutHandle(LayoutHandle):

    @classmethod
    async def from_data(cls, state, layout_handle_resolver):
        base_layout_handle = await layout_handle_resolver.resolve(state.base_layout_handle_ref)
        return base.command_handle(state.command_id, state.layout_ref)

    def __init__(self, ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher, base_layout_handle, command_id):
        super().__init__(ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout, watcher)
        self._base_layout_handle = base_layout_handle
        self._command_id = command_id

    @property
    def title(self):
        return f"Layout for: {self._object_type._t.name}"

    @property
    def data(self):
        base_layout_handle_ref = self._ref_registry.register_object(self._base_layout_handle.data)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        return htypes.layout.command_layout_handle(base_layout_handle_ref, self._command_id, layout_ref)

    @property
    def base_object_type(self):
        return self._base_layout_handle.base_object_type

    @property
    def command_path(self):
        return [*self._base_layout_handle.command_path, self._command_id]

    def process_layout_diffs(self, diff_list):
        assert 0  # todo


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)

        self._layout_handle_cache = {}  # object_type, command path -> layout handle

        services.layout_handle_codereg = AsyncCapsuleRegistry('layout_handle', services.type_resolver)
        services.layout_handle_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.layout_handle_codereg)
        services.layout_handle_codereg.register_type(
            htypes.layout.default_layout_handle,
            DefaultLayoutHandle.from_data,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_layout_resolver,
            services.object_layout_association,
            self._layout_handle_cache,
            self._layout_from_object_type,
            )
        services.layout_handle_codereg.register_type(
            htypes.layout.command_layout_handle, CommandLayoutHandle.from_data, services.layout_handle_resolver)

        self._ref_registry = services.ref_registry
        self._async_ref_resolver = services.async_ref_resolver
        self._object_layout_registry = services.object_layout_registry
        self._object_layout_resolver = services.object_layout_resolver
        self._default_object_layouts = services.default_object_layouts
        self._object_layout_association = services.object_layout_association

        services.layout_handle_from_object_type = self.layout_handle_from_object_type

    async def layout_handle_from_object_type(self, object_type):
        return (await DefaultLayoutHandle.from_object_type(
            object_type,
            self._ref_registry,
            self._async_ref_resolver,
            self._object_layout_resolver,
            self._object_layout_association,
            self._layout_handle_cache,
            self._layout_from_object_type,
            ))

    async def _layout_from_object_type(self, object_type, layout_watcher):
        layout = await self._object_layout_association.resolve(object_type, layout_watcher)
        if layout is None:
            layout = await self._default_object_layouts.construct_default_layout(object_type, layout_watcher, self._object_layout_registry)
        return layout
