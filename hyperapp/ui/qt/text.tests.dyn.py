from . import htypes
from .tested.code import text
from .services import (
    mosaic,
    )
from .code.mark import mark
from .fixtures import qapp_fixtures
from .code.context import Context


@mark.fixture
def adapter():
    accessor = htypes.accessor.model_accessor()
    cvt = htypes.type_convertor.noop_convertor()
    return htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )


@mark.fixture
def view_piece(adapter):
    return htypes.text.readonly_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def edit_piece(adapter):
    return htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture.obj
def state():
    return htypes.text.state('')


def test_view_text(qapp, view_piece, state):
    ctx = Context()
    model = "Sample text"
    view = text.ViewTextView.from_piece(view_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == view_piece
    widget_state = view.widget_state(widget)
    assert widget_state == state, widget_state


def test_edit_text(qapp, edit_piece, state):
    ctx = Context()
    model = "Sample text"
    view = text.EditTextView.from_piece(edit_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == edit_piece
    widget_state = view.widget_state(widget)
    assert widget_state == state


@mark.fixture
def accessor():
    return htypes.accessor.model_accessor()


def test_view_factory(accessor):
    piece = text.text_view(htypes.builtin.string, accessor)
    assert piece


def test_edit_factory(accessor):
    piece = text.text_edit(htypes.builtin.string, accessor)
    assert piece
