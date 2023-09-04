import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    )

log = logging.getLogger(__name__)

DUP_OFFSET = htypes.window.pos(150, 50)


class WindowCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMainWindow()
        w.setCentralWidget(QtWidgets.QLabel("Hello!"))
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w


@mark.ui_command(htypes.window.layout)
def duplicate(layout, state):
    log.info("Duplicate window: %s / %s", layout, state)
