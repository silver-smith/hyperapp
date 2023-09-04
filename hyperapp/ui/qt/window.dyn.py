from PySide6 import QtWidgets

from . import htypes
from .services import (
    web,
    )

DUP_OFFSET = htypes.window.pos(150, 50)


class AppCtl:

    @classmethod
    def from_piece(cls, layout):
        window_ctl_list = [
            WindowCtl.from_piece(web.summon(l))
            for l in layout.window_list
            ]
        return cls(window_ctl_list)

    def __init__(self, window_ctl_list):
        self._window_ctl_list = window_ctl_list

    def construct_widget(self, state, ctx):
        return [
            ctl.construct_widget(web.summon(s), ctx)
            for ctl, s in zip(self._window_ctl_list, state.window_list)
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
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w

    def duplicate(self, widget):
        pass
