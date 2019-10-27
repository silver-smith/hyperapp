import logging
from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after, key_match
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .view import View

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, tab_index):
        self._tab_view = None
        self._tab_index = tab_index

    def set_tab_view(self, tab_view):
        self._tab_view = tab_view

    def open(self, view):
        self._tab_view._replace_view(self._tab_index, view)


class TabView(QtWidgets.QTabWidget, View):

    @classmethod
    async def from_data(cls, state, command_registry, view_resolver):
        children = []
        opener_list = []
        for idx, tab_ref in enumerate(state.tabs):
            opener = _ViewOpener(idx)
            child = await view_resolver.resolve(tab_ref, command_registry, opener)
            opener_list.append(opener)
            children.append(child)
        tab_view = cls(children, state.current_tab)
        for opener in opener_list:
            opener.set_tab_view(tab_view)
        return tab_view

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
        services.view_registry.register_type(htypes.tab_view.tab_view, TabView.from_data, services.view_resolver)
