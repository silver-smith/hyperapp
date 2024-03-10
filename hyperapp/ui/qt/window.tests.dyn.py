from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .code.list_diff import ListDiff
from .code.view import Diff
from .code import menu_bar  # Used implicitly
from .tested.code import window


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.view_layout(mosaic.put(adapter_piece))
    tabs_piece = htypes.tabs.view(
        tabs=[htypes.tabs.tab("One", mosaic.put(text_piece))],
        )
    piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return (tabs_piece, piece)


def make_state():
    text_state = htypes.text.state()
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )
    state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    return (tabs_state, state)


def test_construct_widget():
    command_hub = CommandHub()
    ctx = Context(command_hub=command_hub)
    tabs_piece, piece = make_piece()
    tabs_state, state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = window.WindowView.from_piece(piece)
        assert view.piece
        widget = view.construct_widget(state, ctx)
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate_window():
    tabs_piece, window_piece = make_piece()
    tabs_state, window_state = make_state()
    root_piece = htypes.root.view([mosaic.put(window_piece)])
    root_state = htypes.root.state([mosaic.put(window_state)], 0)
    diff = window.duplicate_window(root_piece, root_state)
    assert diff
