import asyncio
import logging
from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class MenuBar(QtWidgets.QMenuBar):

    @classmethod
    async def from_state(cls, state, command_hub, lcs):
        return cls(lcs, command_hub)

    def __init__(self, lcs, command_hub):
        super().__init__()
        self._lcs = lcs
        self._build()
        self._locale = 'en'
        command_hub.subscribe(self)

    @property
    def state(self):
        return htypes.menu_bar.menu_bar()

    # command hub observer method
    def commands_changed(self, kind, command_list):
        if kind == 'global':
            self._update_menu(self._file_menu, command_list)
        if kind == 'object':
            # Shortcuts for object commands are set by command pane.
            # Do not set them here or qt they treat them as ambiguous overload.
            self._update_menu(self._dir_menu, command_list, add_shortcut=False)
        if kind == 'view':
            self._update_menu(self._view_menu, command_list)

    def _build(self):
        self._file_menu = QtWidgets.QMenu('&File')
        self._dir_menu = QtWidgets.QMenu('&Dir')
        self._view_menu = QtWidgets.QMenu('La&yout')
        self.addMenu(self._file_menu)
        self.addMenu(self._dir_menu)
        self.addMenu(self._view_menu)

    def _update_menu(self, menu, command_list, add_shortcut=True):
        menu.clear()
        for command in command_list:
            menu.addAction(self._make_action(menu, command, add_shortcut))

    def _make_action(self, menu, command, add_shortcut, used_shortcut_set=None):
        text = command.name
        shortcut = self._lcs.get([command.dir, htypes.command.command_shortcut_d()])

        if used_shortcut_set is not None:
            # remove duplicates
            if shortcut in used_shortcut_set:
                shortcut = None
            else:
                used_shortcut_set.add(shortcut)

        action = QtWidgets.QAction(text, menu)
        if add_shortcut and shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(partial(self._run_command, command))
        return action

    def _run_command(self, command):
        asyncio.create_task(command.run())


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.menu_bar.menu_bar, MenuBar.from_state, services.lcs)
