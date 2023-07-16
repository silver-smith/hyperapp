from PySide6 import QtWidgets

from . import htypes
from .tested.code.window import WindowCtl
from .services import (
    mosaic,
    )


def test_window():
    piece = htypes.window.window(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put('phony view'),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    app = QtWidgets.QApplication()
    try:
        w = WindowCtl(piece)
        w.construct_widget(ctx=None)
    finally:
        app.shutdown()
