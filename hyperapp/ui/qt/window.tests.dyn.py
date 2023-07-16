from PySide6 import QtWidgets

from . import htypes
from .tested.code.window import AppCtl
from .services import (
    mosaic,
    )


def test_window():
    layout = htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put('phony view'),
        )
    app_layout = htypes.window.app_layout(mosaic.put(layout))
    state = htypes.window.state(
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    app_state = htypes.window.app_state(
        window_list=[mosaic.put(state)],
        )
    app = QtWidgets.QApplication()
    try:
        w = AppCtl.from_piece(app_layout)
        w.construct_widget(app_state, ctx=None)
    finally:
        app.shutdown()
