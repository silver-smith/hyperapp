from PySide6 import QtWidgets

from . import htypes
from .services import (
    web,
    )


DUP_OFFSET = htypes.window.pos(150, 50)


class AppCtl:

    @classmethod
    def from_piece(cls, layout):
        window_layout = web.summon(layout.window_layout)
        window_ctl = WindowCtl.from_piece(window_layout)
        return cls(window_ctl)

    def __init__(self, window_ctl):
        self._window_ctl = window_ctl

    def construct_widget(self, state, ctx):
        return [
            self._window_ctl.construct_widget(web.summon(ws), ctx)
            for ws in state.window_list
            ]


class WindowCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMainWindow()
        w.setCentralWidget(QtWidgets.QLabel("Hello!"))
        return w

    def duplicate(self, widget):
        pass
