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
        model_d = {htypes.ui.model_command_kind_d()}
        context_d = {htypes.ui.context_model_command_kind_d()}
        global_d = {htypes.ui.global_model_command_kind_d()}
        wanted_commands = {
            cmd for cmd in commands
            if (
                    cmd.d & model_d and not (cmd.d & global_d)
                    or cmd.d & context_d
                )
            }
        removed_commands = set(widget._command_to_button) - wanted_commands
        new_commands = wanted_commands - set(widget._command_to_button)
        for cmd in removed_commands:
            button = widget._command_to_button.pop(cmd)
            button.deleteLater()
        for cmd in new_commands:
            # All except context commands are present at menu bar;
            # avoid setting shortcut to prevent ambigous ones.
            button = cmd.make_button(add_shortcut=cmd.d & context_d)
            layout.addWidget(button)
            widget._command_to_button[cmd] = button
