import asyncio
import itertools
import logging
import weakref
from collections import namedtuple
from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr
from hyperapp.client.util import make_async_action
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view_handler import InsertVisualItemDiff, RemoveVisualItemDiff, RootVisualItem, ViewHandler
from .layout_registry import LayoutViewProducer
from .command_hub import CommandHub

_log = logging.getLogger(__name__)


class LayoutWatcher:

    def __init__(self):
        self._observers = weakref.WeakSet()

    def subscribe(self, observer):
        self._observers.add(observer)

    def distribute_diffs(self, diff_list):
        for observer in self._observers:
            observer.process_layout_diffs(diff_list)


class RootHandler(ViewHandler):

    class _WindowRec:

        def __init__(self, id, on_close, window_commands):
            self.id = id
            self._on_close = on_close
            self._window_commands = window_commands
            self._command_hub = CommandHub(get_commands=self.get_current_commands)

        async def _async_init(self, view_resolver, path, ref):
            self.handler = await view_resolver.resolve(ref, [*path, self.id], self._window_closed, self._command_hub)

        def get_current_commands(self):
            root_commands = [command.partial(self.id) for command in self._window_commands]
            return [*self.handler.get_current_commands(), *root_commands]

        def _window_closed(self):
            self._on_close(self.id)

    @classmethod
    async def from_data(cls, state, path, ref_registry, view_resolver, layout_watcher):
        self = cls(ref_registry, view_resolver, layout_watcher, path)
        await self._async_init(state.window_ref_list)
        return self

    def __init__(self, ref_registry, view_resolver, layout_watcher, path):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._view_resolver = view_resolver
        self._layout_watcher = layout_watcher
        self._window_list = None
        self._rec_id_counter = itertools.count()

    async def _async_init(self, window_ref_list):
        self._window_rec_list = [
            await self._create_window_rec(ref)
            for idx, ref in enumerate(window_ref_list)
            ]

    def get_view_ref(self):
        window_ref_list = [rec.handler.get_view_ref() for rec in self._window_rec_list]
        root_layout = htypes.root_layout.root_layout(window_ref_list)
        return self._ref_registry.register_object(root_layout)

    async def create_view(self):
        self._window_list = window_list = [
            await rec.handler.create_view()
            for rec in self._window_rec_list
            ]
        for window in window_list:
            window.show()
        return window_list

    async def visual_item(self):
        children = [
            await rec.handler.visual_item()
            for rec in self._window_rec_list
            ]
        return RootVisualItem('Root', children=[
            child.to_item(idx, f'window#{idx}', list(self._window_visual_commands(idx)))
            for idx, child in enumerate(children)
            ])

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            rec.handler for rec in self._window_rec_list)

    async def _create_window_rec(self, ref):
        window_commands = self.get_command_list()
        rec = self._WindowRec(next(self._rec_id_counter), self._on_window_closed, window_commands)
        await rec._async_init(self._view_resolver, self._path, ref)
        return rec

    def _window_visual_commands(self, idx):
        rec = self._window_rec_list[idx]
        for command in self.get_command_list():
            if command.id == 'quit':
                continue
            resource_key = command.resource_key
            path = [*resource_key.path[:-1], 'visual_' + resource_key.path[-1]]
            resource_key = resource_key_t(resource_key.base_ref, path)
            yield (command
                   .wrap(self._run_command_for_item)
                   .with_resource_key(resource_key)
                   )

    async def _run_command_for_item(self, command, item_path):
        idx, rec = self._find_rec(item_path[-1])
        return (await command.run(rec.id))

    def _on_window_closed(self, rec_id):
        if len(self._window_rec_list) == 1:
            return  # closing last window means exit
        idx, rec = self._find_rec(rec_id)
        del self._window_list[idx]
        del self._window_rec_list[idx]
        self._layout_watcher.distribute_diffs([
            RemoveVisualItemDiff([*self._path, rec_id])])

    @command('quit')
    def _quit(self, rec_id):
        QtWidgets.QApplication.quit()

    @command('duplicate_window')
    async def _duplicate_window(self, rec_id):
        idx, rec = self._find_rec(rec_id)
        new_idx, new_rec = await self._duplicate_window_impl(idx, rec)
        #self._widget.setCurrentIndex(new_idx)
        item = await new_rec.handler.visual_item()
        self._layout_watcher.distribute_diffs([
            InsertVisualItemDiff(self._path, new_idx, item)])

    async def _duplicate_window_impl(self, idx, rec):
        new_idx = idx + 1
        ref = rec.handler.get_view_ref()
        new_rec = await self._create_and_insert_rec(idx, ref)
        return (new_idx, new_rec)

    async def _create_and_insert_rec(self, idx, ref):
        rec = await self._create_window_rec(ref)
        window = await rec.handler.create_view()
        window.show()
        self._window_rec_list.insert(idx, rec)
        self._window_list.insert(idx, window)
        return rec

    def _find_rec(self, rec_id):
        for idx, rec in enumerate(self._window_rec_list):
            if rec.id == rec_id:
                return (idx, rec)
        assert False, f"Wrong window record id: {rec_id}"


class LayoutManager:

    def __init__(self, view_producer_registry, view_registry):
        self._view_producer_registry = view_producer_registry
        self._view_registry = view_registry
        self._root_handler = None
        self._window_list = None

    async def create_layout_views(self, root_view):
        # root path is expected by layout editor to be [0]
        self._root_handler = handler = await self._view_registry.resolve_async(root_view, [0])
        self._window_list = await handler.create_view()

    @property
    def root_handler(self):
        return self._root_handler

    async def produce_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))


class ViewProducer(LayoutViewProducer):

    def __init__(self, view_producer_registry):
        self._view_producer_registry = view_producer_registry

    async def produce_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))

    async def produce_default_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))


class ViewOpener:

    def __init__(self, layout_manager):
        self._layout_manager = layout_manager

    async def open_rec(self, rec):
        await self._layout_manager.open(rec)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_watcher = LayoutWatcher()
        services.layout_manager = layout_manager = LayoutManager(
            services.view_producer_registry,
            services.view_registry,
            )
        services.view_registry.register_type(
            htypes.root_layout.root_layout, RootHandler.from_data, services.ref_registry, services.view_resolver, services.layout_watcher)
        services.view_producer = ViewProducer(layout_manager)
        services.view_opener = ViewOpener(layout_manager)
