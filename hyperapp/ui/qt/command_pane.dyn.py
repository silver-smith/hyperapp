import logging
from functools import partial

from PySide6 import QtCore, QtWidgets

from . import htypes
from .code.mark import mark
from .code.view import Item, View
from .code.command import command_text

log = logging.getLogger(__name__)


class CommandPane(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.command_to_button = {}
        self.spacing_idx = None


class CommandPaneView(View):

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
        return htypes.command_pane.view()

    def construct_widget(self, state, ctx):
        w = CommandPane()
        layout = QtWidgets.QVBoxLayout(w, spacing=1)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addSpacing(10)
        w.spacing_idx = 0
        return w

    def widget_state(self, widget):
        return htypes.command_pane.state()

    def secondary_parent_context(self, rctx, widget):
        used_shortcuts = set()
        for button in widget.command_to_button.values():
            shortcut = button.shortcut()
            if shortcut:
                used_shortcuts.add(shortcut.toString())
        return rctx.clone_with(
            used_shortcuts=used_shortcuts,
            )

    async def children_changed(self, ctx, rctx, widget):
        commands = rctx.get('commands', [])
        pane_1_d = htypes.command_groups.pane_1_d()
        pane_2_d = htypes.command_groups.pane_2_d()
        layout = widget.layout()
        new_commands = {
            cmd for cmd in commands
            if {pane_1_d, pane_2_d} & cmd.groups
            }
        removed_commands = set(widget.command_to_button) - new_commands
        widget.spacing_idx -= sum(1 for cmd in removed_commands if pane_1_d in cmd.groups)
        new_commands = new_commands - set(widget.command_to_button)
        for cmd in removed_commands:
            button = widget.command_to_button.pop(cmd)
            button.deleteLater()
        used_shortcuts = set()
        for cmd in new_commands:
            button = self._make_button(cmd, used_shortcuts)
            if pane_1_d in cmd.groups:
                layout.insertWidget(widget.spacing_idx, button)
            else:
                layout.addWidget(button)
            widget.command_to_button[cmd] = button
        widget.spacing_idx += sum(1 for cmd in new_commands if pane_1_d in cmd.groups)

    def _make_button(self, cmd, used_shortcuts):
        text = command_text(self._format, cmd)
        shortcut = self._shortcut_reg.get(cmd.d)
        if shortcut:
            text += f' ({shortcut})'
        button = QtWidgets.QPushButton(
            text, focusPolicy=QtCore.Qt.NoFocus, enabled=cmd.enabled)
        button.pressed.connect(cmd.start)
        if shortcut and shortcut not in used_shortcuts:
            button.setShortcut(shortcut)
            used_shortcuts.add(shortcut)
        tooltip = str(cmd.d)
        if not cmd.enabled:
            tooltip += '\n' + cmd.disabled_reason
        button.setToolTip(tooltip)
        return button
