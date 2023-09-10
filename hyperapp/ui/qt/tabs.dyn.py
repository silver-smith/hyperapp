import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    )

log = logging.getLogger(__name__)


class TabsCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTabWidget()
        w.addTab(QtWidgets.QLabel("Hello!"), "First")
        return w


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
