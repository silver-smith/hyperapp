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
from .code.view import Item, View

log = logging.getLogger(__name__)

DUP_OFFSET = htypes.window.pos(150, 50)


class WindowView(View):

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def construct_widget(self, piece, state, ctx):
        menu_bar_piece = web.summon(piece.menu_bar_ref)
        central_view_piece = web.summon(piece.central_view_ref)
        menu_bar_view = ui_ctl_creg.animate(menu_bar_piece)
        central_view = ui_ctl_creg.animate(central_view_piece)
        w = QtWidgets.QMainWindow()
        central_view_state = web.summon(state.central_view_state)
        menu_bar_state = web.summon(state.menu_bar_state)
        central_widget = central_view.construct_widget(central_view_piece, central_view_state, ctx)
        menu_bar = menu_bar_view.construct_widget(menu_bar_piece, menu_bar_state, ctx)
        w.setMenuBar(menu_bar)
        w.setCentralWidget(central_widget)
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w

    def get_current(self, piece, widget):
        return 1

    def widget_state(self, piece, widget):
        menu_bar_piece = web.summon(piece.menu_bar_ref)
        central_view_piece = web.summon(piece.central_view_ref)
        menu_bar_view = ui_ctl_creg.animate(menu_bar_piece)
        central_view = ui_ctl_creg.animate(central_view_piece)
        menu_bar_state = menu_bar_view.widget_state(menu_bar_piece, widget.menuBar())
        central_view_state = central_view.widget_state(central_view_piece, widget.centralWidget())
        return htypes.window.state(
            menu_bar_state=mosaic.put(menu_bar_state),
            central_view_state=mosaic.put(central_view_state),
            size=htypes.window.size(widget.width(), widget.height()),
            pos=htypes.window.pos(widget.x(), widget.y()),
            )

    def apply(self, ctx, piece, widget, layout_diff, state_diff):
        central_view_piece = web.summon(piece.central_view_ref)
        central_view = ui_ctl_creg.animate(central_view_piece)
        result = central_view.apply(
            ctx, central_view_piece, widget.centralWidget(), layout_diff, state_diff)
        if result is None:
            return None
        new_central_piece, new_central_state, replace = result
        assert not replace  # Not yet supported.
        new_piece = htypes.window.layout(
            menu_bar_ref=piece.menu_bar_ref,
            command_pane_ref=piece.command_pane_ref,
            central_view_ref=mosaic.put(new_central_piece),
            )
        return (new_piece, self.widget_state(new_piece, widget), False)

    def items(self, piece, widget):
        return [
            Item('menu bar', piece.menu_bar_ref, widget.menuBar()),
            Item('central', piece.central_view_ref, widget.centralWidget()),
            ]


@mark.ui_command(htypes.root.view)
def duplicate_window(layout, state):
    log.info("Duplicate window: %s / %s", layout, state)
    layout_diff = ListDiff.Insert(
        idx=state.current + 1,
        item=layout.window_list[state.current],
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
    state_diff = ListDiff.Insert(
        idx=state.current + 1,
        item=mosaic.put(new_window_state),
        )
    return (layout_diff, state_diff)
