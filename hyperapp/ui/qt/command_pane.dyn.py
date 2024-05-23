import logging
from functools import partial

from PySide6 import QtCore, QtWidgets

from . import htypes
from .code.view import Item, View

log = logging.getLogger(__name__)


class CommandPane(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self._command_to_button = {}


class CommandPaneView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        return cls()

    def __init__(self):
        super().__init__()

    @property
    def piece(self):
        return htypes.command_pane.view()

    def construct_widget(self, state, ctx):
        w = CommandPane()
        layout = QtWidgets.QVBoxLayout(w, spacing=1)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(2, 2, 2, 2)
        return w

    def widget_state(self, widget):
        return htypes.command_pane.state()

    def set_commands(self, widget, commands):
        layout = widget.layout()
        # wanted_commands = {
        #     cmd for cmd in commands
        #     if (
        #             cmd.d & model_d and not (cmd.d & global_d)
        #             or cmd.d & context_d
        #         )
        #     }
        wanted_commands = {
            cmd for cmd in commands
            if self._show_command(cmd.groups)
            }
        removed_commands = set(widget._command_to_button) - wanted_commands
        new_commands = wanted_commands - set(widget._command_to_button)
        for cmd in removed_commands:
            button = widget._command_to_button.pop(cmd)
            button.deleteLater()
        for cmd in new_commands:
            # All except context commands are present at menu bar;
            # avoid setting shortcut to prevent ambigous ones.
            # button = self._make_button(cmd, add_shortcut=cmd.d & context_d)
            button = self._make_button(cmd, add_shortcut=True)  # TODO
            layout.addWidget(button)
            widget._command_to_button[cmd] = button

    def _show_command(self, groups):
        context_d = htypes.command_groups.context_d()
        if context_d in groups:
            return True
        return False

    @staticmethod
    def _make_button(cmd, add_shortcut):
        text = cmd.name
        if cmd.shortcut:
            text += f' ({cmd.shortcut})'
        button = QtWidgets.QPushButton(
            text, focusPolicy=QtCore.Qt.NoFocus, enabled=cmd.enabled)
        button.pressed.connect(cmd.start)
        if add_shortcut and cmd.shortcut:
            button.setShortcut(cmd.shortcut)
        if not cmd.enabled:
            button.setToolTip(cmd.disabled_reason)
        return button
