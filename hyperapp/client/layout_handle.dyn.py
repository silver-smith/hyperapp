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


class LayoutHandle:

    @classmethod
    async def from_data(cls, state, object, layout_handle_registry):
        handle = await layout_handle_registry.produce_handle(object, category=state.category)
        return handle

    def __init__(self, ref_registry, object_layout_association, category, layout, watcher, path=None):
        self._ref_registry = ref_registry
        self._object_layout_association = object_layout_association
        self._category = category
        self._path = path or []
        self._layout = layout
        self._watcher = watcher
        self._watcher.subscribe(self)

    @property
    def data(self):
        return htypes.layout.layout_handle(self._category, self._path)

    @property
    def title(self):
        if self._path:
            return self._category + '/' + '/'.join(self._path)
        else:
            return self._category

    @property
    def layout(self):
        return self._layout

    @property
    def watcher(self) -> LayoutWatcher:
        return self._watcher

    async def set_layout(self, layout):
        self._layout = layout
        item = await layout.visual_item()
        self._watcher.distribute_diffs([UpdateVisualItemDiff(['root'], item)])

    def process_layout_diffs(self, diff_list):
        layout_ref = self._ref_registry.register_object(self._layout.data)
        self._object_layout_association[self._category] = layout_ref


class LayoutHandleRegistry:

    def __init__(
            self,
            ref_registry,
            async_ref_resolver,
            default_object_layouts,
            object_layout_association,
            object_layout_registry,
            ):
        self._ref_registry = ref_registry
        self._async_ref_resolver = async_ref_resolver
        self._default_object_layouts = default_object_layouts
        self._object_layout_association = object_layout_association
        self._object_layout_registry = object_layout_registry
        self._handle_registry = weakref.WeakValueDictionary()  # (category, command path) -> LayoutHandle

    async def produce_handle(self, object, path=('root',), category=None):
        if not category:
            category = object.category_list[-1]
        try:
            return self._handle_registry[category, ()]
        except KeyError:
            pass
        _log.info("Produce layout handle for category %r of object %s", category, object)
        try:
            layout_ref = self._object_layout_association[category]
        except KeyError:
            rec_it = self._default_object_layouts.resolve(object.category_list)
            try:
                rec = next(rec_it)
            except StopIteration:
                raise NoSuitableProducer(f"No producers are registered for categories {object.category_list}")
            _log.info("Use default layout %r.", rec.name)
            layout_rec = await rec.layout_rec_maker(object)
        else:
            _log.info("Use layout associated to %r.", category)
            layout_rec = await self._async_ref_resolver.resolve_ref_to_object(layout_ref)
        watcher = LayoutWatcher()
        layout = await self._object_layout_registry.resolve_async(layout_rec, list(path), object, watcher)
        handle = LayoutHandle(self._ref_registry, self._object_layout_association, category, layout, watcher)
        self._handle_registry[category, ()] = handle
        return handle


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_handle_registry = LayoutHandleRegistry(
            services.ref_registry,
            services.async_ref_resolver,
            services.default_object_layouts,
            services.object_layout_association,
            services.object_layout_registry,
            )
        services.layout_handle_codereg = AsyncCapsuleRegistry('layout_handle', services.type_resolver)
        services.layout_handle_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.layout_handle_codereg)
        services.layout_handle_codereg.register_type(htypes.layout.layout_handle, LayoutHandle.from_data, services.layout_handle_registry)
