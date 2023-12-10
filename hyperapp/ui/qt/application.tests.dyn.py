from PySide6 import QtWidgets

from . import htypes
from .code.window import WindowCtl  # unused
from .tested.code import application
from .services import (
    mosaic,
    )
from .code.context import Context


def make_layout():
    text_layout = htypes.text.view_layout()
    tabs_layout = htypes.tabs.layout(
        tabs=[htypes.tabs.tab("One", mosaic.put(text_layout))],
        )
    window_layout = htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.layout()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put(tabs_layout),
        )
    return htypes.application.layout(
        window_list=[mosaic.put(window_layout)],
        )


def make_state():
    text_state = htypes.text.state("Sample text")
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    return htypes.application.state(
        window_list=[mosaic.put(window_state)],
        )


def test_app():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = application.AppCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
    finally:
        app.shutdown()
