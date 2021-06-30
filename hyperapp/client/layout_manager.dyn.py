import asyncio
import itertools
import logging
from collections import namedtuple
from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr

from . import htypes
from .command import command
from .layout_handle import InsertVisualItemDiff, RemoveVisualItemDiff, LayoutWatcher
from .layout import GlobalLayout
from .command_hub import CommandHub
from .module import ClientModule

_log = logging.getLogger(__name__)


class RootLayout(GlobalLayout):

    class _WindowRec:

        def __init__(self, id, on_close, window_commands):
            self.id = id
            self._on_close = on_close
            self._window_commands = window_commands
            self._command_hub = CommandHub(get_commands=self.get_current_commands)

        async def _async_init(self, view_registry, path, ref):
            self.layout = await view_registry.invite(ref, [*path, self.id], self._window_closed, self._command_hub)

        async def get_current_commands(self):
            layout_commands = await self.layout.get_current_commands()
            # root_commands = [command.partial(self.id) for command in self._window_commands]
            root_commands = self._window_commands
            return [*layout_commands, *root_commands]

        async def update_commands(self):
            await self._command_hub.update()

        def _window_closed(self):
            self._on_close(self.id)

    @classmethod
    async def from_data(cls, state, path, async_stop_event, mosaic, view_registry, layout_watcher):
        self = cls(async_stop_event, mosaic, view_registry, layout_watcher, path)
        await self._async_init(state.window_ref_list)
        return self

    def __init__(self, async_stop_event, mosaic, view_registry, layout_watcher, path):
        super().__init__(path)
        self._async_stop_event = async_stop_event
        self._mosaic = mosaic
        self._view_registry = view_registry
        self._layout_watcher = layout_watcher
        self._window_list = None
        self._rec_id_counter = itertools.count()

    async def _async_init(self, window_ref_list):
        self._window_rec_list = [
            await self._create_window_rec(ref)
            for idx, ref in enumerate(window_ref_list)
            ]

    @property
    def piece(self):
        window_ref_list = [
            self._mosaic.put(rec.layout.piece)
            for rec in self._window_rec_list
            ]
        return htypes.root_layout.root_layout(window_ref_list)

    async def create_view(self):
        self._window_list = window_list = [
            await rec.layout.create_view()
            for rec in self._window_rec_list
            ]
        for window in window_list:
            window.show()
        return window_list

    async def visual_item(self):
        children = [
            await rec.layout.visual_item()
            for rec in self._window_rec_list
            ]
        return self.make_visual_item('Root', children=[
            child.with_added_commands(self._window_visual_commands(idx))
            for idx, child in enumerate(children)
            ])

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            rec.layout for rec in self._window_rec_list)

    async def update_commands(self):
        for rec in self._window_rec_list:
            await rec.update_commands()

    async def _create_window_rec(self, ref):
        window_commands = self.get_command_list()
        rec = self._WindowRec(f'window#{next(self._rec_id_counter)}', self._on_window_closed, window_commands)
        await rec._async_init(self._view_registry, self._path, ref)
        return rec

    def _window_visual_commands(self, idx):
        rec = self._window_rec_list[idx]
        for command in self.get_all_command_list():
            if command.id == 'quit':
                continue
            yield (command
                   .with_(kind='element')
                   .with_(params_subst=self._subst_params_for_item)
                   )

    def _subst_params_for_item(self, item_path, *args, **kw):
        idx, rec = self._find_rec(item_path[-1])
        return ((rec.id, *args), kw)

    def _on_window_closed(self, rec_id):
        if len(self._window_rec_list) == 1:
            # Closing last window means exit.
            self._async_stop_event.set()
            return  # Do not remove last window from list - we will need to store it to state.
        idx, rec = self._find_rec(rec_id)
        del self._window_list[idx]
        del self._window_rec_list[idx]
        self._layout_watcher.distribute_diffs([
            RemoveVisualItemDiff([*self._path, rec_id])])

    @command
    def _quit(self, rec_id):
        self._async_stop_event.set()

    @command
    async def _duplicate_window(self, rec_id):
        idx, rec = self._find_rec(rec_id)
        new_idx, new_rec = await self._duplicate_window_impl(idx, rec)
        #self._widget.setCurrentIndex(new_idx)
        item = await new_rec.layout.visual_item()
        self._layout_watcher.distribute_diffs([
            InsertVisualItemDiff(self._path, new_idx, item)])

    async def _duplicate_window_impl(self, idx, rec):
        new_idx = idx + 1
        ref = self._mosaic.put(rec.layout.piece)
        new_rec = await self._create_and_insert_rec(idx, ref)
        return (new_idx, new_rec)

    async def _create_and_insert_rec(self, idx, ref):
        rec = await self._create_window_rec(ref)
        window = await rec.layout.create_view()
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

    def __init__(self, view_registry):
        self._view_registry = view_registry
        self._root_layout = None
        self._window_list = None

    async def create_layout_views(self, root_layout_state):
        # root path is expected by layout editor to be ['root']
        self._root_layout = layout = await self._view_registry.animate(root_layout_state, ['root'])
        self._window_list = await layout.create_view()

    @property
    def root_layout(self):
        return self._root_layout


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.layout_watcher = LayoutWatcher()
        services.layout_manager = layout_manager = LayoutManager(
            services.view_registry,
            )
        services.view_registry.register_actor(
            htypes.root_layout.root_layout, RootLayout.from_data, services.async_stop_event,
            services.mosaic, services.view_registry, services.layout_watcher)
