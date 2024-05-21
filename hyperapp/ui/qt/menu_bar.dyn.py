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
        model_d = {htypes.ui.model_command_kind_d()}
        context_d = {htypes.ui.context_model_command_kind_d()}
        global_d = {htypes.ui.global_model_command_kind_d()}
        global_menu, view_menu, current_menu = [
            action.menu() for action in w.actions()
            ]
        removed_commands = set(w._command_to_action) - set(commands)
        for cmd in removed_commands:
            action = w._command_to_action.pop(cmd)
            global_menu.removeAction(action)
        for cmd in commands:
            if cmd.d & context_d:
                continue
            if cmd.d & global_d:
                menu = global_menu
            elif cmd.d & model_d:
                menu = current_menu
            else:
                menu = view_menu
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
