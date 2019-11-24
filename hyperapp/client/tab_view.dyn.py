import logging
from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .view_registry import InsertVisualItemDiff, RootVisualItem, ViewHandler

log = logging.getLogger(__name__)


class TabViewHandler(ViewHandler):

    @classmethod
    async def from_data(cls, state, path, view_resolver):
        self = cls(state, path, view_resolver)
        await self._async_init()
        return self

    def __init__(self, state, path, view_resolver):
        super().__init__()
        self._tab_list = state.tabs
        self._current_tab = state.current_tab
        self._path = path
        self._view_resolver = view_resolver
        self._tab_handler_list = None

    async def _async_init(self):
        self._tab_handler_list = [
            await self._view_resolver.resolve(tab_ref, [*self._path, idx])
            for idx, tab_ref in enumerate(self._tab_list)]

    async def create_view(self, command_registry, view_opener=None):
        children = []
        opener_list = []
        for idx, tab_handler in enumerate(self._tab_handler_list):
            opener = _ViewOpener(idx)
            child = await tab_handler.create_view(command_registry, opener)
            opener_list.append(opener)
            children.append(child)
        tab_view = TabView(children, self._current_tab)
        for opener in opener_list:
            opener.set_tab_view(tab_view)
        return tab_view

    async def visual_item(self):
        children = [await self._visual_item(idx)
                    for idx in range(len(self._tab_handler_list))]
        return RootVisualItem('TabView', children)

    async def _visual_item(self, idx):
        tab_handler = self._tab_handler_list[idx]
        child = await tab_handler.visual_item()
        commands = [self._duplicate_tab.partial(idx)]
        return child.to_item(idx, f'tab#{idx}', commands)

    @command('duplicate_tab')
    async def _duplicate_tab(self, tab_idx, item_path):
        tab_ref = self._tab_list[tab_idx]
        idx = tab_idx + 1
        tab_handler = await self._view_resolver.resolve(tab_ref, [*self._path, idx])
        self._tab_list.insert(idx, tab_ref)
        self._tab_handler_list.insert(idx, tab_handler)
        item = await self._visual_item(idx)
        return InsertVisualItemDiff([*self._path, idx], item)


class _ViewOpener:

    def __init__(self, tab_index):
        self._tab_view = None
        self._tab_index = tab_index

    def set_tab_view(self, tab_view):
        self._tab_view = tab_view

    def open(self, view):
        self._tab_view._replace_view(self._tab_index, view)


class TabView(QtWidgets.QTabWidget, View):

    def __init__(self, children, current_tab):
        QtWidgets.QTabWidget.__init__(self)
        View.__init__(self)
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)
        self.setElideMode(QtCore.Qt.ElideMiddle)
        for view in children:
            self.addTab(view, view.get_title())
        self.setCurrentIndex(current_tab)

    def _replace_view(self, idx, view):
        old_widget = self.widget(idx)
        self.removeTab(idx)
        old_widget.deleteLater()
        self.insertTab(idx, view.get_widget(), view.get_title())
        view.ensure_has_focus()

    def setVisible(self, visible):
        QtWidgets.QTabWidget.setVisible(self, visible)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(htypes.tab_view.tab_view, TabViewHandler.from_data, services.view_resolver)
