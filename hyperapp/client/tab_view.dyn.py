import asyncio
import logging
import itertools
from collections import namedtuple

from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst

from . import htypes
from .util import DEBUG_FOCUS, call_after, key_match
from .view import View
from .command import command
from .layout import GlobalLayout
from .module import ClientModule

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, layout, tab_name):
        self._layout = layout
        self._tab_name = tab_name

    def open(self, view):
        self._layout._replace_tab(self._tab_name, view)


class TabLayout(GlobalLayout):

    _Tab = namedtuple('_Tab', 'name layout')

    @classmethod
    async def from_data(cls, state, path, command_hub, view_opener, mosaic, view_registry, layout_watcher):
        self = cls(mosaic, view_registry, layout_watcher, state.current_tab, path, command_hub, view_opener)
        await self._async_init(state.tabs)
        return self

    def __init__(self, mosaic, view_registry, layout_watcher, current_tab_idx, path, command_hub, view_opener):
        super().__init__(path)
        self._mosaic = mosaic
        self._view_registry = view_registry
        self._initial_tab_idx = current_tab_idx  # valid only during construction
        self._layout_watcher = layout_watcher
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._tab_id_counter = itertools.count()
        self._widget = None

    async def _async_init(self, tab_ref_list):
        self._tab_list = [
            await self._create_tab(tab_ref)
            for tab_ref in tab_ref_list
            ]

    @property
    def piece(self):
        tab_ref_list = [
            self._mosaic.put(tab.layout.piece)
            for tab in self._tab_list
            ]
        if self._widget:
            if self._widget.currentIndex() != -1:
                current_tab = self._widget.currentIndex()
            else:
                current_tab = 0
        else:
            current_tab = self._initial_tab_idx
        return htypes.tab_view.tab_view(tab_ref_list, current_tab)

    async def create_view(self):
        children = [await tab.layout.create_view() for tab in self._tab_list]
        tab_view = TabView(children, self._initial_tab_idx, on_current_tab_changed=self._on_current_tab_changed)
        self._widget = tab_view
        return tab_view

    async def visual_item(self):
        children = [await self._visual_item(tab)
                    for tab in self._tab_list]
        return self.make_visual_item('TabView', children=children)

    async def get_current_commands(self):
        if not self._widget:
            return []
        tab_idx = self._widget.currentIndex()
        if tab_idx == -1:
            return []
        current_layout = self._tab_list[tab_idx].layout
        # my_commands = [
        #     command.with_(params_subst=self._subst_params_for_current_tab)
        #     for command in self.get_command_list()
        #     ]
        my_commands = self.get_command_list()
        return self._merge_commands(
            await current_layout.get_current_commands(),
            my_commands,
            )

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            tab.layout for tab in self._tab_list)

    async def _visual_item(self, tab):
        child = await tab.layout.visual_item()
        commands = [
            command
              .with_(kind='element')
              .with_(params_subst=self._subst_params_for_item)
            for command in self.get_all_command_list()
            ]
        return child.with_added_commands(commands)

    async def _create_tab(self, tab_ref):
        tab_id = next(self._tab_id_counter)
        tab_name = f'tab#{tab_id}'
        opener = _ViewOpener(self, tab_name)
        layout = await self._view_registry.invite(tab_ref, [*self._path, tab_name], self._command_hub, opener)
        return self._Tab(tab_name, layout)

    def _on_current_tab_changed(self, tab_idx):
        if tab_idx != -1:
            asyncio.create_task(self._command_hub.update())

    def _find_tab(self, tab_name):
        for idx, tab in enumerate(self._tab_list):
            if tab.name == tab_name:
                return idx
        assert False, f"Wrong tab id: {tab_name}"

    def _subst_params_for_current_tab(self, *args, **kw):
        tab_idx = self._widget.currentIndex()
        return ((tab_idx, *args), kw)

    def _subst_params_for_item(self, item_path, *args, **kw):
        tab_idx = self._find_tab(item_path[-1])
        return ((tab_idx, *args), kw)

    def _replace_tab(self, tab_name, view):
        tab_idx = self._find_tab(tab_name)
        if self._widget:
            self._widget.replace_tab(tab_idx, view)

    # @command
    # async def add_tab(self, tab_idx, view_ref: LayoutRecMakerField):
    #     await self._create_and_insert_tab(tab_idx, view_ref)

    @command
    async def duplicate_tab(self, tab_idx):
        tab = self._tab_list[tab_idx]
        tab_ref = self._mosaic.put(tab.layout.piece)
        await self._create_and_insert_tab(tab_idx, tab_ref)

    async def _create_and_insert_tab(self, tab_idx, tab_ref):
        tab = await self._create_tab(tab_ref)
        self._tab_list.insert(tab_idx, tab)
        if self._widget:
            view = await tab.layout.create_view()
            self._widget.insert_tab(tab_idx, view)
        new_idx = tab_idx + 1
        if self._widget:
            self._widget.setCurrentIndex(new_idx)
            await self._command_hub.update()
        item = await self._visual_item(tab)
        self._layout_watcher.distribute_diffs([InsertVisualItemDiff(self._path, new_idx, item)])

    @command
    def close_tab(self, tab_idx):
        tab = self._tab_list[tab_idx]
        del self._tab_list[tab_idx]
        if self._widget:
            self._widget.remove_tab(tab_idx)
        self._layout_watcher.distribute_diffs([RemoveVisualItemDiff([*self._path, tab.name])])

    # @command
    # async def visual_add_nested_tabs(self, item_path):
    #     tab_idx, tab = self._find_tab(item_path[-1])
    #     new_idx = len(self._tab_list)
    #     tab_ref = this_module._new_tab_ref
    #     new_tab = await self._create_and_insert_tab(tab_idx, tab_ref)
    #     item = await self._visual_item(new_tab)
    #     return [InsertVisualItemDiff(self._path, new_idx, item)]

    @command
    async def wrap_with_tabs(self, tab_idx, tab):
        remove_diff_list = [
            RemoveVisualItemDiff([*self._path, tab.name])
            for tab in self._tab_list]
        old_count = len(self._tab_list)
        new_tab = await self._create_tab(self._mosaic.put(self.piece))
        self._tab_list = [new_tab]
        if self._widget:
            while self._widget.count() > 1:
                self._widget.remove_tab(1)
            view = await new_tab.layout.create_view()
            self._widget.replace_tab(0, view)
        item = await self._visual_item(new_tab)
        self._layout_watcher.distribute_diffs([
            *remove_diff_list,
            InsertVisualItemDiff(self._path, 0, item),
            ])


class TabView(QtWidgets.QTabWidget, View):

    def __init__(self, children, current_tab, on_current_tab_changed):
        QtWidgets.QTabWidget.__init__(self)
        View.__init__(self)
        self._on_current_tab_changed = on_current_tab_changed
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)  # does not work...
        self.setElideMode(QtCore.Qt.ElideMiddle)
        for view in children:
            self.addTab(view, view.title)
        self.setCurrentIndex(current_tab)
        self.currentChanged.connect(self._on_current_tab_changed)

    def setVisible(self, visible):
        QtWidgets.QTabWidget.setVisible(self, visible)

    def get_current_child(self):
        return self.currentWidget()

    def replace_tab(self, tab_idx, view):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()
        self.insertTab(tab_idx, view.get_widget(), view.title)
        self.setCurrentIndex(tab_idx)  # lost when old tab removed
        view.ensure_has_focus()

    def insert_tab(self, tab_idx, view):
        self.insertTab(tab_idx, view.get_widget(), view.title)
        view.ensure_has_focus()

    def remove_tab(self, tab_idx):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        services.view_registry.register_actor(
            htypes.tab_view.tab_view, TabLayout.from_data, services.mosaic, services.view_registry, services.layout_watcher)
        services.available_view_registry['tab_view'] = self._make_new_tab_ref()

    def _make_new_tab_ref(self):
        piece = "New tab"
        piece_ref = self._mosaic.put(piece)
        navigator = htypes.navigator.navigator(piece_ref, origin_dir=[])
        navigator_ref = self._mosaic.put(navigator)
        tab_view = htypes.tab_view.tab_view([navigator_ref], 0)
        return self._mosaic.put(tab_view)
