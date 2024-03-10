from PySide6 import QtWidgets

from . import htypes
from .tested.code import text
from .services import (
    mosaic,
    )
from .code.context import Context


def make_adapter():
    return htypes.str_adapter.static_str_adapter("Sample text")


def make_view_piece():
    adapter_layout = make_adapter()
    return htypes.text.readonly_view(mosaic.put(adapter_layout))


def make_edit_piece():
    adapter_layout = make_adapter()
    return htypes.text.edit_layout(mosaic.put(adapter_layout))


def make_state():
    return htypes.text.state()


def test_view_text():
    ctx = Context()
    piece = make_view_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = text.ViewTextView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_edit_text():
    ctx = Context()
    piece = make_edit_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = text.EditTextView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
