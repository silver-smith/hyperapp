import logging

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)

from . import htypes
from .code.mark import mark
from .code.view import View


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self):
        super().__init__()
        self.command_to_action = {}


class MenuBarView(View):

    @classmethod
    @mark.actor.view_creg
    def from_piece(cls, piece, ctx):
        return cls()

    def __init__(self):
        super().__init__()

    @property
    def piece(self):
        return htypes.menu_bar.view()

    def construct_widget(self, state, ctx):
        widget = MenuBar()
        for text in ['&Global', '&View', '&Current']:
            widget.addMenu(QtWidgets.QMenu(text, toolTipsVisible=True))
        return widget

    def widget_state(self, widget):
        return htypes.menu_bar.state()

    async def children_context_changed(self, ctx, rctx, widget):
        commands = rctx.commands
        used_shortcuts = rctx.get('used_shortcuts', set())
        global_d = htypes.command_groups.global_d()
        view_d = htypes.command_groups.view_d()
        model_d = htypes.command_groups.model_d()

        global_menu, view_menu, model_menu = [
            action.menu() for action in widget.actions()
            ]
        removed_commands = set(widget.command_to_action) - set(commands)
        for cmd in removed_commands:
            action = widget.command_to_action.pop(cmd)
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
            action = self._make_action(cmd, used_shortcuts)
            menu.addAction(action)
            widget.command_to_action[cmd] = action

    @staticmethod
    def _make_action(cmd, used_shortcuts):
        action = QtGui.QAction(cmd.name, enabled=cmd.enabled)
        action.triggered.connect(cmd.start)
        if cmd.shortcut and cmd.shortcut not in used_shortcuts:
            action.setShortcut(cmd.shortcut)
        if not cmd.enabled:
            action.setToolTip(cmd.disabled_reason)
        return action
