from PySide6 import QtWidgets

from . import htypes
from .tested.code.window import AppCtl, WindowCtl
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


def test_app():
    app_layout = htypes.window.app_layout(
        window_list=[mosaic.put(make_window_layout())],
    )
    app_state = htypes.window.app_state(
        window_list=[mosaic.put(make_window_state())],
        )
    app = QtWidgets.QApplication()
    try:
        ctl = AppCtl.from_piece(app_layout)
        widget = ctl.construct_widget(app_state, ctx=None)
    finally:
        app.shutdown()


def test_window():
    layout = make_window_layout()
    state = make_window_state()
    app = QtWidgets.QApplication()
    try:
        ctl = WindowCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx=None)
        ctl.duplicate(widget)
    finally:
        app.shutdown()
