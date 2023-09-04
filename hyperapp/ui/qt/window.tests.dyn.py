from PySide6 import QtWidgets

from . import htypes
from .tested.code.window import WindowCtl, duplicate
from .services import (
    mosaic,
    )


def make_window_layout():
    return htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put('phony view'),
        )


def make_window_state():
    return htypes.window.state(
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )


def test_window():
    layout = make_window_layout()
    state = make_window_state()
    app = QtWidgets.QApplication()
    try:
        ctl = WindowCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx=None)
    finally:
        app.shutdown()


def test_duplicate():
    layout = make_window_layout()
    state = make_window_state()
    duplicate(layout, state)
