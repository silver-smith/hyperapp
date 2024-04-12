import logging
from functools import partial

from PySide6 import QtCore, QtWidgets

from . import htypes
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)


class CommandPane(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self._command_to_button = {}


class CommandPaneView(View):

    @classmethod
    def from_piece(cls, piece):
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
        filter_d = htypes.ui.model_command_kind_d()
        wanted_commands = {
            cmd for cmd in commands
            if filter_d in cmd.d
            }
        removed_commands = set(widget._command_to_button) - wanted_commands
        new_commands = wanted_commands - set(widget._command_to_button)
        for cmd in removed_commands:
            button = widget._command_to_button.pop(cmd)
            button.deleteLater()
        for cmd in new_commands:
            button = cmd.make_button()
            layout.addWidget(button)
            widget._command_to_button[cmd] = button
