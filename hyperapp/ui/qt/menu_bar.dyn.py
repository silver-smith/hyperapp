import logging

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)

from . import htypes
from .code.view import View


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self):
        super().__init__()
        self._command_to_action = {}


class MenuBarView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        return cls()

    def __init__(self):
        super().__init__()

    @property
    def piece(self):
        return htypes.menu_bar.view()

    def construct_widget(self, state, ctx):
        w = MenuBar()
        for text in ['&Global', '&View', '&Current']:
            w.addMenu(QtWidgets.QMenu(text, toolTipsVisible=True))
        return w

    def widget_state(self, widget):
        return htypes.menu_bar.state()

    def set_commands(self, w, commands):
        global_d = htypes.command_groups.global_d()
        view_d = htypes.command_groups.view_d()
        model_d = htypes.command_groups.model_d()

        global_menu, view_menu, model_menu = [
            action.menu() for action in w.actions()
            ]
        removed_commands = set(w._command_to_action) - set(commands)
        for cmd in removed_commands:
            action = w._command_to_action.pop(cmd)
            global_menu.removeAction(action)
        for cmd in commands:
            if global_d in cmd.groups:
                menu = global_menu
            elif view_d in cmd.groups:
                menu = view_menu
            elif model_d in cmd.groups:
                menu = model_menu
            else:
                continue
            action = self._make_action(cmd)
            menu.addAction(action)
            w._command_to_action[cmd] = action

    @staticmethod
    def _make_action(cmd):
        action = QtGui.QAction(cmd.name, enabled=cmd.enabled)
        action.triggered.connect(cmd.start)
        if cmd.shortcut:
            action.setShortcut(cmd.shortcut)
        if not cmd.enabled:
            action.setToolTip(cmd.disabled_reason)
        return action
