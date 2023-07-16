from PySide6 import QtWidgets

from . import htypes
from .services import (
    web,
    )


DUP_OFFSET = htypes.window.pos(150, 50)


class AppCtl:

    def __init__(self, layout):
        self._window_ctl = WindowCtl(layout.window_layout)

    def construct_widget(self, state, ctx):
        return [
            self._window_ctl.construct_widget(web.summon(ws), ctx)
            for ws in state.window_list
            ]


class WindowCtl:

    def __init__(self, layout):
        super().__init__()

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMainWindow()
        w.setCentralWidget(QtWidgets.QLabel("Hello!"))
        return w

    def duplicate(self, widget):
        pass
