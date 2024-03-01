import logging
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)

DUP_OFFSET = htypes.window.pos(150, 50)


class WindowView(View):

    @classmethod
    def from_piece(cls, piece):
        menu_bar_view = ui_ctl_creg.invite(piece.menu_bar_ref)
        central_view = ui_ctl_creg.invite(piece.central_view_ref)
        return cls(menu_bar_view, central_view)

    def __init__(self, menu_bar_view, central_view):
        super().__init__()
        self._menu_bar_view = menu_bar_view
        self._central_view = central_view

    @property
    def piece(self):
        return htypes.window.layout(
            menu_bar_ref=mosaic.put(self._menu_bar_view.piece),
            central_view_ref=mosaic.put(self._central_view.piece),
            )

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMainWindow()
        central_view_state = web.summon(state.central_view_state)
        menu_bar_state = web.summon(state.menu_bar_state)
        central_widget = self._central_view.construct_widget(central_view_state, ctx)
        menu_bar = self._menu_bar_view.construct_widget(menu_bar_state, ctx)
        w.setMenuBar(menu_bar)
        w.setCentralWidget(central_widget)
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w

    def get_current(self, widget):
        return 1

    def widget_state(self, widget):
        menu_bar_state = self._menu_bar_view.widget_state(widget.menuBar())
        central_view_state = self._central_view.widget_state(widget.centralWidget())
        return htypes.window.state(
            menu_bar_state=mosaic.put(menu_bar_state),
            central_view_state=mosaic.put(central_view_state),
            size=htypes.window.size(widget.width(), widget.height()),
            pos=htypes.window.pos(widget.x(), widget.y()),
            )

    def apply(self, ctx, widget, diff):
        raise NotImplementedError(f"Not implemented: window.apply({diff.piece})")

    def items(self, widget):
        return [
            Item('menu bar', self._menu_bar_view, widget.menuBar()),
            Item('central', self._central_view, widget.centralWidget()),
            ]


@mark.ui_command(htypes.root.view)
def duplicate_window(piece, state):
    log.info("Duplicate window: %s / %s", piece, state)
    diff_piece = ListDiff.Insert(
        idx=state.current + 1,
        item=piece.window_list[state.current],
        )
    window_state = web.summon(state.window_list[state.current])
    new_window_state = htypes.window.state(
        menu_bar_state=window_state.menu_bar_state,
        central_view_state=window_state.central_view_state,
        size=window_state.size,
        pos=htypes.window.pos(
            x=window_state.pos.x + DUP_OFFSET.x,
            y=window_state.pos.y + DUP_OFFSET.y,
            ),
        )
    diff_state = ListDiff.Insert(
        idx=state.current + 1,
        item=mosaic.put(new_window_state),
        )
    return Diff(diff_piece, diff_state)
