import asyncio
import logging
from functools import partial

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)


_hardcoded_shortcuts = {
    'back': ['Escape'],
    'forward': ['Alt+Right'],
    'duplicate': ['Shift+f4', 'Ctrl+f4'],
    'static_text_1': ['f1'],
    'static_text_2': ['f2'],
    'static_list': ['f3'],
    'fn_list': ['f4'],
    }


class MenuBarCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        self._menu_command_to_action = {}
        self._used_shortcuts = set()

    def construct_widget(self, state, ctx):
        w =  QtWidgets.QMenuBar()
        ctx.command_hub.subscribe(partial(self.commands_changed, w))
        return w

    def set_commands(self, w, commands):
        w.clear()
        self._used_shortcuts.clear()
        self._command_to_action = {}
        menu = QtWidgets.QMenu('&All')
        for command in commands:
            self._add_action(menu, command)
        w.addMenu(menu)

    def commands_changed(self, w, removed_commands, added_commands):
        [menu_action] = w.actions()
        menu = menu_action.menu()
        for command in removed_commands:
            action = self._menu_command_to_action[menu, command]
            menu.removeAction(action)
            self._used_shortcuts.remove(action.shortcut())
        for command in added_commands:
            self._add_action(menu, command)

    def _add_action(self, menu, command):
        action = QtGui.QAction(command.name, menu)
        action.triggered.connect(partial(self._run_command, command))
        for name, shortcut_list in _hardcoded_shortcuts.items():
            if name not in command.name:
                continue
            for shortcut in shortcut_list:
                if shortcut not in self._used_shortcuts:
                    action.setShortcut(shortcut)
                    self._used_shortcuts.add(shortcut)
                    break
        menu.addAction(action)
        self._menu_command_to_action[menu, command] = action

    def _run_command(self, command):
        log.info("Run command: %r", command.name)
        asyncio.create_task(command.run())
