from PySide6 import QtWidgets

from . import htypes
from .tested.code.window import WindowCtl
from .services import (
    mosaic,
    )
from .code.context import Context


def make_layout():
    tabs_layout = htypes.tabs.layout(
        tab_list=[mosaic.put("Nothing is here")],
        )
    return htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.layout()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put(tabs_layout),
        )


def make_state():
    tabs_state = htypes.tabs.state(
        current_tab=0,
        )
    return htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )


def test_window():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = WindowCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
    finally:
        app.shutdown()
