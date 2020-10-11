import logging
import weakref
from dataclasses import dataclass
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


class LayoutHandle:

    def __init__(
            self, ref_registry, object_layout_resolver, object_layout_association, layout_handle_cache, layout_from_object_type,
            watcher, object_type, origin_object_type, origin_command_id, layout):
        self._ref_registry = ref_registry
        self._object_layout_resolver = object_layout_resolver
        self._layout_handle_cache = layout_handle_cache
        self._layout_from_object_type = layout_from_object_type
        self._object_type = object_type
        self._origin_object_type = origin_object_type
        self._origin_command_id = origin_command_id
        self._watcher = watcher
        self._layout = layout
        self._watcher.subscribe(self)

    @property
    def title(self):
        if self._origin_object_type:
            return f"For: {self._origin_object_type._t.name}/{self._origin_command_id}"
        else:
            return f"For type: {self._object_type._t.name}"

    @property
    def data(self):
        object_type_ref = self._ref_registry.register_object(self._object_type)
        if self._origin_object_type:
            origin_object_type_ref = self._ref_registry.register_object(self._object_type)
        else:
            origin_object_type_ref = None
        return htypes.layout.layout_handle(object_type_ref, origin_object_type_ref, self._origin_command_id)

    @property
    def layout(self):
        return self._layout

    @property
    def watcher(self) -> LayoutWatcher:
        return self._watcher

    async def command_handle(self, command_id, object_type, layout_ref):
        try:
            return self._layout_handle_cache[object_type]
        except KeyError:
            pass
        watcher = LayoutWatcher()
        if layout_ref:
            layout = await self._object_layout_resolver.resolve(layout_ref, ['root'], watcher)
        else:
            layout = await self._layout_from_object_type(object_type, watcher)
        handle = LayoutHandle(
            self._ref_registry, self._object_layout_resolver, self._object_layout_association, self._layout_handle_cache, self._layout_from_object_type,
            watcher, object_type, self._object_type, command_id, layout)
        self._layout_handle_cache[object_type] = handle
        return handle

    async def set_layout(self, layout):
        self._layout = layout
        item = await layout.visual_item()
        self._watcher.distribute_diffs([UpdateVisualItemDiff(['root'], item)])

    def process_layout_diffs(self, diff_list):
        _log.info("Save layout association for %r to %s", self._layout.object_type, self._layout.data)
        self._object_layout_association.associate(self._object_type, self._layout)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)

        self._layout_handle_cache = {}  # object_type path -> layout handle

        services.layout_handle_from_data = self.layout_handle_from_data
        services.layout_handle_from_ref = self.layout_handle_from_ref

        self._ref_registry = services.ref_registry
        self._async_ref_resolver = services.async_ref_resolver
        self._object_layout_registry = services.object_layout_registry
        self._object_layout_resolver = services.object_layout_resolver
        self._default_object_layouts = services.default_object_layouts
        self._object_layout_association = services.object_layout_association

        services.layout_handle_from_object_type = self.layout_handle_from_object_type

    async def layout_handle_from_object_type(self, object_type):
        return (await self._create_layout_handle(object_type))

    async def layout_handle_from_ref(self, state_ref):
        state = await self._async_ref_resolver.resolve_ref_to_object(state_ref)
        return (await self.layout_handle_from_data(state))

    async def layout_handle_from_data(self, state):
        object_type = await self._async_ref_resolver.resolve_ref_to_object(state.object_type_ref)
        if state.origin_object_type_ref:
            origin_object_type = await self._async_ref_resolver.resolve_ref_to_object(state.origin_object_type_ref)
        else:
            origin_object_type = None
        return (await self._create_layout_handle(object_type, origin_object_type, state.origin_command_id))

    async def _create_layout_handle(self, object_type, origin_object_type=None, origin_command_id=None):
        try:
            return self._layout_handle_cache[object_type]
        except KeyError:
            pass
        watcher = LayoutWatcher()
        layout = await self._layout_from_object_type(object_type, watcher)
        handle = LayoutHandle(
            self._ref_registry, self._object_layout_resolver, self._object_layout_association, self._layout_handle_cache, self._layout_from_object_type,
            watcher, object_type, origin_object_type, origin_command_id, layout)
        self._layout_handle_cache[object_type] = handle
        return handle

    async def _layout_from_object_type(self, object_type, layout_watcher):
        layout = await self._object_layout_association.resolve(object_type, layout_watcher)
        if layout is None:
            layout = await self._default_object_layouts.construct_default_layout(object_type, layout_watcher, self._object_layout_registry)
        return layout
