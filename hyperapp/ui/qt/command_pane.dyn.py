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
        self._spacing_idx = None


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
        layout.addSpacing(10)
        w._spacing_idx = 0
        return w

    def widget_state(self, widget):
        return htypes.command_pane.state()

    async def children_context_changed(self, ctx, rctx, widget):
        commands = rctx.commands
        pane_1_d = htypes.command_groups.pane_1_d()
        pane_2_d = htypes.command_groups.pane_2_d()
        layout = widget.layout()
        new_commands = {
            cmd for cmd in commands
            if {pane_1_d, pane_2_d} & cmd.groups
            }
        removed_commands = set(widget._command_to_button) - new_commands
        widget._spacing_idx -= sum(1 for cmd in removed_commands if pane_1_d in cmd.groups)
        new_commands = new_commands - set(widget._command_to_button)
        for cmd in removed_commands:
            button = widget._command_to_button.pop(cmd)
            button.deleteLater()
        for cmd in new_commands:
            # All except context commands are present at menu bar;
            # avoid setting shortcut to prevent ambigous ones.
            button = self._make_button(cmd, add_shortcut=True)
            if pane_1_d in cmd.groups:
                layout.insertWidget(widget._spacing_idx, button)
            else:
                layout.addWidget(button)
            widget._command_to_button[cmd] = button
        widget._spacing_idx += sum(1 for cmd in new_commands if pane_1_d in cmd.groups)

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
