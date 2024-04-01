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
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w, spacing=1)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(2, 2, 2, 2)
        return w

    def widget_state(self, widget):
        return htypes.command_pane.state()

    def commands_changed(self, widget, removed_commands, added_commands):
        layout = widget.layout()
        for command in removed_commands:
            if command.name in _skip_commands:
                continue
            command.button.deleteLater()
        for command in added_commands:
            if command.name in _skip_commands:
                continue
            layout.addWidget(command.button)
