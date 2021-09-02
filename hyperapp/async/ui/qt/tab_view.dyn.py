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
        self = cls(mosaic, view_registry, command_hub, children, state.current_tab)
        return self

    def __init__(self, mosaic, view_registry, command_hub, children, current_tab):
        QtWidgets.QTabWidget.__init__(self)
        View.__init__(self)
        self._mosaic = mosaic
        self._view_registry = view_registry
        self._command_hub = command_hub
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)  # does not work...
        self.setElideMode(QtCore.Qt.ElideMiddle)
        self._tab_list = children
        for view in children:
            self.addTab(view.qt_widget, view.title)
        self.setCurrentIndex(current_tab)
        self.currentChanged.connect(self._on_current_tab_changed)

    @property
    def state(self):
        return htypes.tab_view.state(
            tab_view_ref_list=[
                self._mosaic.put(tab.state)
                for tab in self._tab_list
                ],
            current_tab=self.currentIndex(),
            )

    def iter_view_commands(self):
        for idx, tab in enumerate(self._tab_list):
            for path, command in tab.iter_view_commands():
                yield ([f"tab#{idx}", *path], command)

    async def get_current_commands(self):
        child = self._tab_list[self.currentIndex()]
        return [
            *await child.get_current_commands(),
            *self.get_command_list(),
            ]

    def replace_qt_widget(self, view):
        idx = self._tab_list.index(view)
        self.replace_tab(idx, view)

    def setVisible(self, visible):
        QtWidgets.QTabWidget.setVisible(self, visible)

    def get_current_child(self):
        return self.currentWidget()

    def _on_current_tab_changed(self, tab_idx):
        if tab_idx != -1:
            asyncio.create_task(self._command_hub.update())

    @command
    async def duplicate_tab(self):
        idx = self.currentIndex()
        state = self._tab_list[idx].state
        view = await self._view_registry.animate(state, self._command_hub)
        self.insert_tab(idx + 1, view)
        await self._command_hub.update()

    def replace_tab(self, tab_idx, view):
        old_widget = self.widget(tab_idx)
        self.removeTab(tab_idx)
        old_widget.deleteLater()
        self.insertTab(tab_idx, view.qt_widget, view.title)
        self.setCurrentIndex(tab_idx)  # lost when old tab removed
        view.ensure_has_focus()

    def insert_tab(self, tab_idx, view):
        self.insertTab(tab_idx, view.qt_widget, view.title)
        self._tab_list.insert(tab_idx, view)
        self.setCurrentIndex(tab_idx)
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
