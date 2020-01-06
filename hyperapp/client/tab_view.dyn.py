import logging
from collections import namedtuple

from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .command_hub import CommandHub
from .view_handler import InsertVisualItemDiff, RemoveVisualItemDiff, RootVisualItem, ViewHandler

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, handler, tab_index):
        self._handler = handler
        self._tab_index = tab_index

    def open(self, view):
        self._handler._replace_tab(self._tab_index, view)


class _CommandsObserver:

    def __init__(self, handler, tab_idx):
        self._handler = handler
        self._tab_idx = tab_idx

    def commands_changed(self, kind, command_list):
        self._handler._tab_commands_changed(self._tab_idx, kind, command_list)


class TabViewHandler(ViewHandler):

    _Tab = namedtuple('_Tab', 'ref commands_observer command_hub handler')

    @classmethod
    async def from_data(cls, state, path, command_hub, view_opener, ref_registry, view_resolver):
        self = cls(ref_registry, view_resolver, state.current_tab, path, command_hub, view_opener)
        await self._async_init(state.tabs)
        return self

    def __init__(self, ref_registry, view_resolver, current_tab_idx, path, command_hub, view_opener):
        super().__init__()
        self._ref_registry = ref_registry
        self._view_resolver = view_resolver
        self._current_tab_idx = current_tab_idx  # valid only during construction
        self._path = path
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._widget = None

    async def _async_init(self, tab_ref_list):
        self._tab_list = [
            await self._create_tab(tab_idx, tab_ref)
            for tab_idx, tab_ref in enumerate(tab_ref_list)
            ]

    def get_view_ref(self):
        tab_refs = [tab.handler.get_view_ref() for tab in self._tab_list]
        if self._widget:
            if self._widget.currentIndex() != -1:
                current_tab = self._widget.currentIndex()
            else:
                current_tab = 0
        else:
            current_tab = self._current_tab_idx
        view = htypes.tab_view.tab_view(tab_refs, current_tab)
        return self._ref_registry.register_object(view)

    async def create_view(self):
        children = [await tab.handler.create_view() for tab in self._tab_list]
        tab_view = TabView(children, self._current_tab_idx, on_current_tab_changed=self._update_commands)
        self._widget = tab_view
        self._update_commands(self._current_tab_idx)
        return tab_view

    async def visual_item(self):
        children = [await self._visual_item(idx)
                    for idx in range(len(self._tab_list))]
        return RootVisualItem('TabView', children)

    async def _visual_item(self, idx):
        tab = self._tab_list[idx]
        child = await tab.handler.visual_item()
        commands = [
            self._visual_duplicate_tab.partial(idx),
            self._visual_close_tab.partial(idx),
            ]
        return child.to_item(idx, f'tab#{idx}', commands)

    async def _create_tab(self, tab_idx, tab_ref):
        command_hub = CommandHub()
        opener = _ViewOpener(self, tab_idx)
        handler = await self._view_resolver.resolve(tab_ref, [*self._path, tab_idx], command_hub, opener)
        observer = _CommandsObserver(self, tab_idx)
        command_hub.subscribe(observer)
        return self._Tab(tab_ref, observer, command_hub, handler)

    def _tab_commands_changed(self, tab_idx, kind, command_list):
        if not self._widget:
            return
        if self._widget.currentIndex() != tab_idx:
            return
        command_list = self._tab_list[tab_idx].command_hub.get_kind_commands(kind)
        self._command_hub.set_kind_commands(kind, command_list)

    def _update_commands(self, tab_idx):
        if tab_idx == -1:
            return
        tab_commands = self._tab_list[tab_idx].command_hub.get_commands()
        view_command_list = [
            *tab_commands.get('view', []),
            self._duplicate_tab.partial(tab_idx),
            self._close_tab.partial(tab_idx),
            ]
        commands = {**tab_commands, 'view': view_command_list}
        self._command_hub.set_commands(commands)

    def _replace_tab(self, tab_idx, view):
        if self._widget:
            self._widget._replace_tab(tab_idx, view)

    @command('visual_duplicate_tab')
    async def _visual_duplicate_tab(self, tab_idx, item_path):
        new_idx = await self._duplicate_tab_impl(tab_idx)
        item = await self._visual_item(new_idx)
        return InsertVisualItemDiff([*self._path, new_idx], item)

    @command('duplicate_tab')
    async def _duplicate_tab(self, tab_idx):
        new_idx = await self._duplicate_tab_impl(tab_idx)
        self._widget.setCurrentIndex(new_idx)

    async def _duplicate_tab_impl(self, tab_idx):
        new_idx = tab_idx + 1
        tab_ref = self._tab_list[tab_idx].ref
        tab = await self._create_tab(new_idx, tab_ref)
        self._tab_list.insert(new_idx, tab)
        if self._widget:
            view = await tab.handler.create_view()
            self._widget.insert_tab(new_idx, view)
        return new_idx

    @command('visual_close_tab')
    def _visual_close_tab(self, tab_idx, item_path):
        del self._tab_list[tab_idx]
        if self._widget:
            self._widget.remove_tab(tab_idx)
        return RemoveVisualItemDiff([*self._path, tab_idx])

    @command('close_tab')
    def _close_tab(self, tab_idx):
        del self._tab_list[tab_idx]
        self._widget.remove_tab(tab_idx)


class TabView(QtWidgets.QTabWidget, View):

    def __init__(self, children, current_tab, on_current_tab_changed):
        QtWidgets.QTabWidget.__init__(self)
        View.__init__(self)
        self._on_current_tab_changed = on_current_tab_changed
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)
        self.setElideMode(QtCore.Qt.ElideMiddle)
        for view in children:
            self.addTab(view, view.get_title())
        self.setCurrentIndex(current_tab)
        self.currentChanged.connect(self._on_current_tab_changed)

    def setVisible(self, visible):
        QtWidgets.QTabWidget.setVisible(self, visible)

    def _replace_tab(self, tab_idx, view):
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
