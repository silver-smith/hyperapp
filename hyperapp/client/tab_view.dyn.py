import logging
from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .view_registry import Item, VisualTree, ViewHandler

log = logging.getLogger(__name__)


class TabViewHandler(ViewHandler):

    def __init__(self, state, view_resolver):
        super().__init__()
        self._state = state
        self._view_resolver = view_resolver
        self._tab_handler_list = None

    async def _ensure_handlers_created(self):
        if self._tab_handler_list is None:
            self._tab_handler_list = []
            for tab_ref in self._state.tabs:
                handler = await self._view_resolver.resolve(tab_ref)
                self._tab_handler_list.append(handler)

    async def create_view(self, command_registry, view_opener=None):
        await self._ensure_handlers_created()
        children = []
        opener_list = []
        for idx, tab_handler in enumerate(self._tab_handler_list):
            opener = _ViewOpener(idx)
            child = await tab_handler.create_view(command_registry, opener)
            opener_list.append(opener)
            children.append(child)
        tab_view = TabView(children, self._state.current_tab)
        for opener in opener_list:
            opener.set_tab_view(tab_view)
        return tab_view

    async def visual_tree(self):
        await self._ensure_handlers_created()
        items = []
        sub_items = {}
        for idx, tab_handler in enumerate(self._tab_handler_list):
            child = await tab_handler.visual_tree()
            items.append(Item(idx, f'tab#{idx}', child.name, [self._duplicate_tab.partial(idx)]))
            sub_items = {(idx,) + key: value for key, value in child.items.items()}
        return VisualTree('TabView', {(): items, **sub_items})

    @command('duplicate_tab')
    async def _duplicate_tab(self, tab_idx, item_path):
        assert 0


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
        services.view_registry.register_type(htypes.tab_view.tab_view, TabViewHandler, services.view_resolver)
