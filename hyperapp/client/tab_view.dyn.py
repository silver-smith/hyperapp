import logging
from collections import namedtuple

from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .command_registry import CommandRegistry
from .view_handler import InsertVisualItemDiff, RootVisualItem, ViewHandler

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

    _Tab = namedtuple('_Tab', 'ref commands_observer command_registry handler')

    @classmethod
    async def from_data(cls, state, path, command_registry, view_opener, view_resolver):
        self = cls(state.current_tab, path, command_registry, view_opener, view_resolver)
        await self._async_init(state.tabs)
        return self

    def __init__(self, current_tab_idx, path, command_registry, view_opener, view_resolver):
        super().__init__()
        self._current_tab_idx = current_tab_idx  # valid only during construction
        self._path = path
        self._command_registry = command_registry
        self._view_opener = view_opener
        self._view_resolver = view_resolver
        self._widget = None

    async def _async_init(self, tab_ref_list):
        self._tab_list = [
            await self._create_tab(tab_idx, tab_ref)
            for tab_idx, tab_ref in enumerate(tab_ref_list)
            ]

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
        commands = [self._visual_duplicate_tab.partial(idx)]
        return child.to_item(idx, f'tab#{idx}', commands)

    async def _create_tab(self, tab_idx, tab_ref):
        command_registry = CommandRegistry()
        opener = _ViewOpener(self, tab_idx)
        handler = await self._view_resolver.resolve(tab_ref, [*self._path, tab_idx], command_registry, opener)
        observer = _CommandsObserver(self, tab_idx)
        command_registry.subscribe(observer)
        return self._Tab(tab_ref, observer, command_registry, handler)

    def _tab_commands_changed(self, tab_idx, kind, command_list):
        if not self._widget:
            return
        if self._widget.currentIndex() != tab_idx:
            return
        command_list = self._tab_list[tab_idx].command_registry.get_kind_commands(kind)
        self._command_registry.set_kind_commands(kind, command_list)

    def _update_commands(self, tab_idx):
        if tab_idx == -1:
            return
        tab_commands = self._tab_list[tab_idx].command_registry.get_commands()
        view_command_list = [
            *tab_commands.get('view', []),
            self._duplicate_tab.partial(tab_idx),
            ]
        commands = {**tab_commands, 'view': view_command_list}
        self._command_registry.set_commands(commands)

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
            self._widget._insert_tab(new_idx, view)
        return new_idx


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

    def _insert_tab(self, tab_idx, view):
        self.insertTab(tab_idx, view.get_widget(), view.get_title())
        view.ensure_has_focus()


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(htypes.tab_view.tab_view, TabViewHandler.from_data, services.view_resolver)
