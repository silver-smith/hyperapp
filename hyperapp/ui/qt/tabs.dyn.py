import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    ui_command_factory,
    )

log = logging.getLogger(__name__)


class TabsCtl:

    @classmethod
    def from_piece(cls, layout):
        commands = ui_command_factory(layout)
        return cls(commands)

    def __init__(self, commands):
        self._commands = commands

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTabWidget()
        w.addTab(QtWidgets.QLabel("Hello!"), "First")
        return w

    def widget_commands(self, widget):
        return [command.bind(widget) for command in self._commands]


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
