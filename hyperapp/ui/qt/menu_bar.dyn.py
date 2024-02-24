import asyncio
import logging
from functools import partial

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)

from . import htypes
from .code.view import View


_hardcoded_shortcuts = {
    'back': ['Esc'],
    'forward': ['Alt+Right'],
    'duplicate': ['Shift+t', 'Shift+f4'],
    'close_tab': ['Ctrl+t', 'Ctrl+f4'],
    'duplicate_window': ['Alt+W'],
    'open_layout_tree': ['Alt+L'],
    'static_text_1': ['f1'],
    'static_text_2': ['f2'],
    'static_list': ['f3'],
    'open_sample_fn_list': ['f4'],
    'open_sample_fn_tree': ['f6'],
    'open_feed_sample_fn_list': ['f5'],
    'open_feed_sample_fn_tree': ['Shift+f6'],
    'show_state': ['Ctrl+Return'],
    'sample_list_state': ['Return'],
    }


class MenuBarView(View):

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        self._menu_command_to_action = {}
        self._used_shortcuts = set()

    def construct_widget(self, piece, state, ctx):
        w =  QtWidgets.QMenuBar()
        menu = QtWidgets.QMenu('&All')
        w.addMenu(menu)
        ctx.command_hub.subscribe(partial(self.commands_changed, w))
        return w

    def widget_state(self, piece, widget):
        return htypes.menu_bar.state()

    def set_commands(self, w, commands):
        [menu_action] = w.actions()
        menu = menu_action.menu()
        menu.clear()
        self._used_shortcuts.clear()
        self._command_to_action = {}
        for command in commands:
            self._add_action(menu, command)

    def commands_changed(self, w, removed_commands, added_commands):
        [menu_action] = w.actions()
        menu = menu_action.menu()
        for command in removed_commands:
            action = self._menu_command_to_action[menu, command]
            menu.removeAction(action)
            try:
                self._used_shortcuts.remove(action.shortcut().toString().upper())
            except KeyError:
                pass
        for command in added_commands:
            self._add_action(menu, command)

    def apply(self, ctx, piece, widget, layout_diff, state_diff):
        raise NotImplementedError()

    def _add_action(self, menu, command):
        action = QtGui.QAction(command.name, menu)
        action.triggered.connect(partial(self._run_command, command))
        for name, shortcut_list in _hardcoded_shortcuts.items():
            if name not in command.name:
                continue
            for shortcut in shortcut_list:
                if shortcut.upper() not in self._used_shortcuts:
                    action.setShortcut(shortcut)
                    self._used_shortcuts.add(shortcut.upper())
                    break
        menu.addAction(action)
        self._menu_command_to_action[menu, command] = action

    def _run_command(self, command):
        log.info("Run command: %r", command.name)
        asyncio.create_task(command.run())
