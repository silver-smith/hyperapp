import logging
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from . import htypes
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)


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
        ctx.command_hub.subscribe(partial(self.commands_changed, w))
        return w

    def widget_state(self, widget):
        return htypes.command_pane.state()

    def commands_changed(self, widget, removed_commands, added_commands):
        layout = widget.layout()
        for idx in range(layout.count()):
            button = layout.itemAt(idx).widget()
            # TODO: Map command to buttons and remove only required.
            button.deleteLater()
        for command in added_commands:
            text = command.name
            if command.shortcut:
                text += f' ({command.shortcut})'
            button = QtWidgets.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
            button.pressed.connect(command.start)
            # if command.shortcut:
            #     button.setShortcut(command.shortcut)
            layout.addWidget(button)
