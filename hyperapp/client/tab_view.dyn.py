import logging
import itertools
from collections import namedtuple

from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .view_handler import InsertVisualItemDiff, RemoveVisualItemDiff, RootVisualItem, ViewHandler

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, handler, tab_id):
        self._handler = handler
        self._tab_id = tab_id

    def open(self, view):
        self._handler._replace_tab(self._tab_id, view)


class TabViewHandler(ViewHandler):

    _Tab = namedtuple('_Tab', 'id handler')

    @classmethod
    async def from_data(cls, state, path, command_hub, view_opener, ref_registry, view_resolver):
        self = cls(ref_registry, view_resolver, state.current_tab, path, command_hub, view_opener)
        await self._async_init(state.tabs)
        return self

    def __init__(self, ref_registry, view_resolver, current_tab_idx, path, command_hub, view_opener):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._view_resolver = view_resolver
        self._initial_tab_idx = current_tab_idx  # valid only during construction
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
        tab_refs = [tab.handler.get_view_ref() for tab in self._tab_list]
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
        children = [await tab.handler.create_view() for tab in self._tab_list]
        tab_view = TabView(children, self._initial_tab_idx, on_current_tab_changed=self._on_current_tab_changed)
        self._widget = tab_view
        return tab_view

    async def visual_item(self):
        children = [await self._visual_item(tab)
                    for tab in self._tab_list]
        return RootVisualItem('TabView', children)

    def get_current_commands(self):
        if self._widget:
            tab_idx = self._widget.currentIndex()
            if tab_idx != -1:
                current_handler = self._tab_list[tab_idx].handler
                return self._get_current_commands_with_child(current_handler)
        return super().get_current_commands()

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            tab.handler for tab in self._tab_list)

    async def _visual_item(self, tab):
        child = await tab.handler.visual_item()
        commands = [
            self._visual_duplicate_tab,
            self._visual_close_tab,
            self._visual_add_nested_tabs,
            self._visual_wrap_with_tabs,
            ]
        return child.to_item(tab.id, f'tab#{tab.id}', commands)

    async def _create_tab(self, tab_ref):
        tab_id = next(self._tab_id_counter)
        opener = _ViewOpener(self, tab_id)
        handler = await self._view_resolver.resolve(tab_ref, [*self._path, tab_id], self._command_hub, opener)
        return self._Tab(tab_id, handler)

    def _on_current_tab_changed(self, tab_idx):
        if tab_idx != -1:
            self._command_hub.update()

    def _find_tab(self, tab_id):
        for idx, tab in enumerate(self._tab_list):
            if tab.id == tab_id:
                return (idx, tab)
        assert False, f"Wront tab id: {tab_id}"

    def _replace_tab(self, tab_id, view):
        tab_idx, _ = self._find_tab(tab_id)
        if self._widget:
            self._widget.replace_tab(tab_idx, view)

    @command('visual_duplicate_tab')
    async def _visual_duplicate_tab(self, item_path):
        tab_idx, tab = self._find_tab(item_path[-1])
        new_idx, new_tab = await self._duplicate_tab_impl(tab_idx, tab)
        item = await self._visual_item(new_tab)
        return [InsertVisualItemDiff(self._path, new_idx, item)]

    @command('duplicate_tab')
    async def _duplicate_tab(self):
        tab_idx = self._widget.currentIndex()
        new_idx, _ = await self._duplicate_tab_impl(tab_idx, self._tab_list[tab_idx])
        self._widget.setCurrentIndex(new_idx)
        self._command_hub.update(new_idx)

    async def _duplicate_tab_impl(self, tab_idx, tab):
        new_idx = tab_idx + 1
        tab_ref = tab.handler.get_view_ref()
        new_tab = await self._create_and_insert_tab(tab_idx, tab_ref)
        return (new_idx, new_tab)

    async def _create_and_insert_tab(self, tab_idx, tab_ref):
        tab = await self._create_tab(tab_ref)
        self._tab_list.insert(tab_idx, tab)
        if self._widget:
            view = await tab.handler.create_view()
            self._widget.insert_tab(tab_idx, view)
        return tab

    @command('visual_close_tab')
    def _visual_close_tab(self, item_path):
        tab_idx, tab = self._find_tab(item_path[-1])
        del self._tab_list[tab_idx]
        if self._widget:
            self._widget.remove_tab(tab_idx)
        return [RemoveVisualItemDiff([*self._path, tab.id])]

    @command('close_tab')
    def _close_tab(self):
        tab_idx = self._widget.currentIndex()
        del self._tab_list[tab_idx]
        self._widget.remove_tab(tab_idx)

    @command('visual_add_nested_tabs')
    async def _visual_add_nested_tabs(self, item_path):
        tab_idx, tab = self._find_tab(item_path[-1])
        new_idx = len(self._tab_list)
        tab_ref = this_module._new_tab_ref
        new_tab = await self._create_and_insert_tab(tab_idx, tab_ref)
        item = await self._visual_item(new_tab)
        return [InsertVisualItemDiff(self._path, new_idx, item)]

    @command('visual_wrap_with_tabs')
    async def _visual_wrap_with_tabs(self, item_path):
        tab_idx, tab = self._find_tab(item_path[-1])
        remove_diff_list = [
            RemoveVisualItemDiff([*self._path, tab.id])
            for tab in self._tab_list]
        old_count = len(self._tab_list)
        new_tab = await self._create_tab(self.get_view_ref())
        self._tab_list = [new_tab]
        if self._widget:
            while self._widget.count() > 1:
                self._widget.remove_tab(1)
            view = await new_tab.handler.create_view()
            self._widget.replace_tab(0, view)
        item = await self._visual_item(new_tab)
        return [*remove_diff_list,
                InsertVisualItemDiff(self._path, 0, item)]


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
            htypes.tab_view.tab_view, TabViewHandler.from_data, services.ref_registry, services.view_resolver)
        services.available_view_registry['tab_view'] = self._new_tab_ref

    @property
    def _new_tab_ref(self):
        piece = htypes.text.text("New tab")
        piece_ref = self._ref_registry.register_object(piece)
        navigator = htypes.navigator.navigator(piece_ref)
        navigator_ref = self._ref_registry.register_object(navigator)
        tab_view = htypes.tab_view.tab_view([navigator_ref], 0)
        return self._ref_registry.register_object(tab_view)
