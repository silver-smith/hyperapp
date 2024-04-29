from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .code import menu_bar  # Used implicitly
from .tested.code import window


def make_window_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    tabs_piece = htypes.tabs.view(
        tabs=(htypes.tabs.tab("One", mosaic.put(text_piece)),),
        )
    piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return (tabs_piece, piece)


def make_window_state():
    text_state = htypes.text.state()
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(text_state),),
        )
    state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    return (tabs_state, state)


def test_construct_widget():
    ctx = Context()
    tabs_piece, piece = make_window_piece()
    tabs_state, state = make_window_state()
    app = QtWidgets.QApplication()
    try:
        view = window.WindowView.from_piece(piece, ctx)
        assert view.piece
        widget = view.construct_widget(state, ctx)
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
