from . import htypes
from .tested.code import text
from .services import (
    mosaic,
    )
from .fixtures import qapp_fixtures
from .code.context import Context


def make_adapter():
    return htypes.str_adapter.static_str_adapter()


def make_view_piece():
    adapter = make_adapter()
    return htypes.text.readonly_view(mosaic.put(adapter))


def make_edit_piece():
    adapter = make_adapter()
    return htypes.text.edit_view(mosaic.put(adapter))


def make_state():
    return htypes.text.state('')


def test_view_text(qapp):
    ctx = Context()
    piece = make_view_piece()
    state = make_state()
    model = "Sample text"
    view = text.ViewTextView.from_piece(piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_edit_text(qapp):
    ctx = Context()
    piece = make_edit_piece()
    state = make_state()
    model = "Sample text"
    view = text.EditTextView.from_piece(piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_view_factory():
    model = "Sample text"
    piece = text.text_view(model, adapter=None)
    assert piece


def test_edit_factory():
    model = "Sample text"
    piece = text.text_edit(model, adapter=None)
    assert piece
