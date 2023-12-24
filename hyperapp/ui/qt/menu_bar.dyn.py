import asyncio
import logging
from functools import partial

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)


class MenuBarCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        self._menu_command_to_action = {}

    def construct_widget(self, state, ctx):
        w =  QtWidgets.QMenuBar()
        ctx.command_hub.subscribe(partial(self.commands_changed, w))
        return w

    def set_commands(self, w, commands):
        w.clear()
        self._command_to_action = {}
        menu = QtWidgets.QMenu('&All')
        for command in commands:
            self._add_action(menu, command)
        w.addMenu(menu)

    def commands_changed(self, w, removed_commands, added_commands):
        [menu_action] = w.actions()
        menu = menu_action.menu()
        for command in removed_commands:
            menu.removeAction(self._menu_command_to_action[menu, command])
        for command in added_commands:
            self._add_action(menu, command)

    def _add_action(self, menu, command):
        idx = len(menu.actions()) + 1
        action = QtGui.QAction(command.name, menu)
        action.triggered.connect(partial(self._run_command, command))
        action.setShortcut(f'f{idx}')
        menu.addAction(action)
        self._menu_command_to_action[menu, command] = action

    def _run_command(self, command):
        log.info("Run command: %r", command.name)
        asyncio.create_task(command.run())
