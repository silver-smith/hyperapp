import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    ui_ctl_creg,
    web,
    )

log = logging.getLogger(__name__)

DUP_OFFSET = htypes.window.pos(150, 50)


class WindowCtl:

    @classmethod
    def from_piece(cls, layout):
        menu_bar_ctl = ui_ctl_creg.invite(layout.menu_bar_ref)
        central_view_ctl = ui_ctl_creg.invite(layout.central_view_ref)
        return cls(menu_bar_ctl, central_view_ctl)

    def __init__(self, menu_bar_ctl, central_view_ctl):
        self._menu_bar_ctl = menu_bar_ctl
        self._central_view_ctl = central_view_ctl

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMainWindow()
        menu_bar_state = web.summon(state.menu_bar_state)
        central_view_state = web.summon(state.central_view_state)
        menu_bar = self._menu_bar_ctl.construct_widget(menu_bar_state, ctx)
        central_widget = self._central_view_ctl.construct_widget(central_view_state, ctx)
        commands = self._central_view_ctl.bind_commands(central_widget)
        w.setMenuWidget(menu_bar)
        w.setCentralWidget(central_widget)
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w
