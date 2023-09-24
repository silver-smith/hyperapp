import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    ui_command_factory,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


class TabsCtl:

    @classmethod
    def from_piece(cls, layout):
        ctl = cls()
        commands = ui_command_factory(layout, ctl)
        ctl._commands = commands
        return ctl

    def __init__(self):
        self._commands = None

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTabWidget()
        w.addTab(QtWidgets.QLabel("Hello!"), "First")
        return w

    def widget_state(self, widget):
        return htypes.tabs.state(current_tab=widget.currentIndex())

    def bind_commands(self, widget):
        return [command.bind(widget) for command in self._commands]


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
    return ListDiff.insert(
        idx=state.current_tab,
        item=layout.tab_list[state.current_tab],
        )
