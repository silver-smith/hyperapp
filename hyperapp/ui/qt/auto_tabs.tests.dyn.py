from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .tested.code import auto_tabs


def make_piece():
    adapter = htypes.str_adapter.static_str_adapter("Sample text")
    text = htypes.text.readonly_view(mosaic.put(adapter))
    return htypes.auto_tabs.view(
        tabs=[mosaic.put(text)],
        )


def make_state():
    text_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )


def test_tabs():
    ctx = Context(command_hub=CommandHub())
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context(command_hub=CommandHub())
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        diff = auto_tabs.duplicate_tab(piece, state)
        replace_widget = view.apply(ctx, widget, diff)
        assert len(view.piece.tabs) == 2
        assert view.piece.tabs[0] == piece.tabs[0]
        assert view.piece.tabs[0] == view.piece.tabs[1]
    finally:
        app.shutdown()


def test_close():
    adapter = htypes.str_adapter.static_str_adapter("Sample text")
    text = htypes.text.readonly_view(mosaic.put(adapter))
    piece = htypes.auto_tabs.view(
        tabs=[
            mosaic.put(text),
            mosaic.put(text),
            ],
        )
    text_state = htypes.text.state()
    state = htypes.tabs.state(
        current_tab=0,
        tabs=[
            mosaic.put(text_state),
            mosaic.put(text_state),
            ],
        )
    ctx = Context(command_hub=CommandHub())
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        diff = auto_tabs.close_tab(piece, state)
        replace_widget = view.apply(ctx, widget, diff)
        assert len(view.piece.tabs) == 1
        assert view.piece.tabs[0] == piece.tabs[1]
    finally:
        app.shutdown()
