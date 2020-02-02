import logging
import itertools
from collections import namedtuple

from PySide2 import QtCore, QtWidgets

from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match, is_list_inst
from hyperapp.common.htypes import resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .layout import InsertVisualItemDiff, RemoveVisualItemDiff, RootVisualItem, Layout

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, layout, tab_id):
        self._layout = layout
        self._tab_id = tab_id

    def open(self, view):
        self._layout._replace_tab(self._tab_id, view)


class TabLayout(Layout):

    _Tab = namedtuple('_Tab', 'id layout')

    @classmethod
    async def from_data(cls, state, path, command_hub, view_opener, ref_registry, view_resolver, layout_watcher):
        self = cls(ref_registry, view_resolver, layout_watcher, state.current_tab, path, command_hub, view_opener)
        await self._async_init(state.tabs)
        return self

    def __init__(self, ref_registry, view_resolver, layout_watcher, current_tab_idx, path, command_hub, view_opener):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._view_resolver = view_resolver
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

    def get_view_ref(self):
        tab_refs = [tab.layout.get_view_ref() for tab in self._tab_list]
        if self._widget:
            if self._widget.currentIndex() != -1:
                current_tab = self._widget.currentIndex()
            else:
                current_tab = 0
        else:
            current_tab = self._initial_tab_idx
        view = htypes.tab_view.tab_view(tab_refs, current_tab)
        return self._ref_registry.register_object(view)

    async def create_view(self):
        children = [await tab.layout.create_view() for tab in self._tab_list]
        tab_view = TabView(children, self._initial_tab_idx, on_current_tab_changed=self._on_current_tab_changed)
        self._widget = tab_view
        return tab_view

    async def visual_item(self):
        children = [await self._visual_item(tab)
                    for tab in self._tab_list]
        return RootVisualItem('TabView', children)

    def get_current_commands(self):
        if not self._widget:
            return []
        tab_idx = self._widget.currentIndex()
        if tab_idx == -1:
            return []
        current_layout = self._tab_list[tab_idx].layout
        my_commands = [
            command.wrap(self._run_command_for_current_tab)
            for command in self.get_command_list()
            ]
        return self._merge_commands(
            current_layout.get_current_commands(),
            my_commands,
            )

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            tab.layout for tab in self._tab_list)

    async def _visual_item(self, tab):
        child = await tab.layout.visual_item()
        commands = [
            command
              .wrap(self._run_command_for_item)
              .with_resource_key(self._element_command_resource_key(command.resource_key))
            for command in self.get_command_list()]
        return child.to_item(tab.id, f'tab#{tab.id}', commands)

    def _element_command_resource_key(self, resource_key):
        path = [*resource_key.path[:-1], 'visual_' + resource_key.path[-1]]
        return resource_key_t(resource_key.base_ref, path)

    async def _create_tab(self, tab_ref):
        tab_id = next(self._tab_id_counter)
        opener = _ViewOpener(self, tab_id)
        layout = await self._view_resolver.resolve(tab_ref, [*self._path, tab_id], self._command_hub, opener)
        return self._Tab(tab_id, layout)

    def _on_current_tab_changed(self, tab_idx):
        if tab_idx != -1:
            self._command_hub.update()

    def _find_tab(self, tab_id):
        for idx, tab in enumerate(self._tab_list):
            if tab.id == tab_id:
                return (idx, tab)
        assert False, f"Wrong tab id: {tab_id}"

    async def _run_command_for_current_tab(self, command):
        tab_idx = self._widget.currentIndex()
        tab = self._tab_list[tab_idx]
        return (await command.run(tab_idx, tab))

    async def _run_command_for_item(self, command, item_path):
        tab_idx, tab = self._find_tab(item_path[-1])
        return (await command.run(tab_idx, tab))

    def _replace_tab(self, tab_id, view):
        tab_idx, _ = self._find_tab(tab_id)
        if self._widget:
            self._widget.replace_tab(tab_idx, view)

    @command('duplicate_tab')
    async def _duplicate_tab(self, tab_idx, tab):
        new_idx = tab_idx + 1
        tab_ref = tab.layout.get_view_ref()
        new_tab = await self._create_and_insert_tab(tab_idx, tab_ref)
        if self._widget:
            self._widget.setCurrentIndex(new_idx)
            self._command_hub.update()
        item = await self._visual_item(new_tab)
        self._layout_watcher.distribute_diffs([InsertVisualItemDiff(self._path, new_idx, item)])

    async def _create_and_insert_tab(self, tab_idx, tab_ref):
        tab = await self._create_tab(tab_ref)
        self._tab_list.insert(tab_idx, tab)
        if self._widget:
            view = await tab.layout.create_view()
            self._widget.insert_tab(tab_idx, view)
        return tab

    @command('close_tab')
    def _close_tab(self, tab_idx, tab):
        del self._tab_list[tab_idx]
        if self._widget:
            self._widget.remove_tab(tab_idx)
        self._layout_watcher.distribute_diffs([RemoveVisualItemDiff([*self._path, tab.id])])

    # @command('visual_add_nested_tabs', kind='element')
    # async def _visual_add_nested_tabs(self, item_path):
    #     tab_idx, tab = self._find_tab(item_path[-1])
    #     new_idx = len(self._tab_list)
    #     tab_ref = this_module._new_tab_ref
    #     new_tab = await self._create_and_insert_tab(tab_idx, tab_ref)
    #     item = await self._visual_item(new_tab)
    #     return [InsertVisualItemDiff(self._path, new_idx, item)]

    @command('wrap_with_tabs')
    async def _wrap_with_tabs(self, tab_idx, tab):
        remove_diff_list = [
            RemoveVisualItemDiff([*self._path, tab.id])
            for tab in self._tab_list]
        old_count = len(self._tab_list)
        new_tab = await self._create_tab(self.get_view_ref())
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
            self.addTab(view, view.get_title())
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
        self.insertTab(tab_idx, view.get_widget(), view.get_title())
        self.setCurrentIndex(tab_idx)  # lost when old tab removed
        view.ensure_has_focus()

    def insert_tab(self, tab_idx, view):
        self.insertTab(tab_idx, view.get_widget(), view.get_title())
        view.ensure_has_focus()

    def remove_tab(self, tab_idx):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        services.view_registry.register_type(
            htypes.tab_view.tab_view, TabLayout.from_data, services.ref_registry, services.view_resolver, services.layout_watcher)
        services.available_view_registry['tab_view'] = self._new_tab_ref

    @property
    def _new_tab_ref(self):
        piece = htypes.text.text("New tab")
        piece_ref = self._ref_registry.register_object(piece)
        navigator = htypes.navigator.navigator(piece_ref)
        navigator_ref = self._ref_registry.register_object(navigator)
        tab_view = htypes.tab_view.tab_view([navigator_ref], 0)
        return self._ref_registry.register_object(tab_view)
