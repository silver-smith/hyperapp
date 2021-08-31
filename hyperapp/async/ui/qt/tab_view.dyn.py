import asyncio
import logging

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .view import View
from .command import command

log = logging.getLogger(__name__)


class _ViewOpener:

    def __init__(self, layout, tab_name):
        self._layout = layout
        self._tab_name = tab_name

    def open(self, view):
        self._layout._replace_tab(self._tab_name, view)


class TabView(QtWidgets.QTabWidget, View):

    @classmethod
    async def from_state(cls, state, command_hub, mosaic, view_registry):
        children = [
            await view_registry.invite(ref, command_hub)
            for ref in state.tab_view_ref_list
            ]
        self = cls(command_hub, children, state.current_tab)
        return self

    def __init__(self, command_hub, children, current_tab):
        QtWidgets.QTabWidget.__init__(self)
        View.__init__(self)
        self._command_hub = command_hub
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)  # does not work...
        self.setElideMode(QtCore.Qt.ElideMiddle)
        self._tab_view_list = children
        for view in children:
            self.addTab(view.qt_widget, view.title)
        self.setCurrentIndex(current_tab)
        self.currentChanged.connect(self._on_current_tab_changed)

    def get_current_commands(self):
        child = self._tab_view_list[self.currentIndex()]
        return child.get_current_commands()

    def replace_qt_widget(self, view):
        idx = self._tab_view_list.index(view)
        self.replace_tab(idx, view)

    def setVisible(self, visible):
        QtWidgets.QTabWidget.setVisible(self, visible)

    def get_current_child(self):
        return self.currentWidget()

    def _on_current_tab_changed(self, tab_idx):
        if tab_idx != -1:
            asyncio.create_task(self._command_hub.update())

    def replace_tab(self, tab_idx, view):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()
        self.insertTab(tab_idx, view.qt_widget, view.title)
        self.setCurrentIndex(tab_idx)  # lost when old tab removed
        view.ensure_has_focus()

    def insert_tab(self, tab_idx, view):
        self.insertTab(tab_idx, view.qt_widget, view.title)
        view.ensure_has_focus()

    def remove_tab(self, tab_idx):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        services.view_registry.register_actor(
            htypes.tab_view.state, TabView.from_state, services.mosaic, services.view_registry)
