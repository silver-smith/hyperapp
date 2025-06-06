import logging

from PySide6 import QtGui, QtWidgets

log = logging.getLogger(__name__)

from . import htypes
from .code.mark import mark
from .code.view import View
from .code.command import command_text


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self):
        super().__init__()
        self.command_to_action = {}


class MenuBarView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, format, shortcut_reg):
        return cls(format, shortcut_reg)

    def __init__(self, format, shortcut_reg):
        super().__init__()
        self._format = format
        self._shortcut_reg = shortcut_reg

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

    async def children_changed(self, ctx, rctx, widget, save_layout):
        commands = rctx.get('commands', [])
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

    def _make_action(self, cmd, used_shortcuts):
        text = command_text(self._format, cmd)
        action = QtGui.QAction(text, enabled=cmd.enabled)
        action.triggered.connect(cmd.start)
        shortcut = self._shortcut_reg.get(cmd.d)
        if shortcut and shortcut not in used_shortcuts:
            action.setShortcut(shortcut)
            used_shortcuts.add(shortcut)
        tooltip = str(cmd.d)
        if not cmd.enabled:
            tooltip += '\n' + cmd.disabled_reason
        action.setToolTip(tooltip)
        return action
