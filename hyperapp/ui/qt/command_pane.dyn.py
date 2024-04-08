import logging
from functools import partial

from PySide6 import QtCore, QtWidgets

from . import htypes
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)


_skip_commands = {
    'duplicate_window',
    'duplicate_tab',
    'close_tab',
    'go_back',
    'go_forward',
    'open_sample_static_text_1',
    'open_sample_static_text_2',
    'open_sample_static_list',
    'open_sample_fn_list',
    'open_feed_sample_fn_list',
    'open_sample_fn_tree',
    'open_feed_sample_fn_tree',
    'open_layout_tree',
    'make_piece',
    'make_state',
    'sample_list',
    }


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
        removed_commands = set(widget._command_to_button) - set(commands)
        new_commands = set(commands) - set(widget._command_to_button)
        for cmd in removed_commands:
            button = widget._command_to_button.pop(cmd)
            button.deleteLater()
        for cmd in new_commands:
            if cmd.name in _skip_commands:
                continue
            button = cmd.make_button()
            layout.addWidget(button)
            widget._command_to_button[cmd] = button
