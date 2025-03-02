from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import line_edit



@mark.fixture
def ctx():
    return Context()


@mark.fixture
def adapter():
    return htypes.str_adapter.static_str_adapter()


@mark.fixture
def view_piece(adapter):
    return htypes.line_edit.readonly_view(mosaic.put(adapter))


@mark.fixture
def edit_piece(adapter):
    return htypes.line_edit.edit_view(mosaic.put(adapter))


@mark.fixture
def state():
    return htypes.line_edit.state('')


def test_edit_view(qapp, ctx, edit_piece, state):
    model = "Sample text"
    view = line_edit.EditLineView.from_piece(edit_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == edit_piece
    state = view.widget_state(widget)
    assert state


def test_readonly_view(qapp, ctx, view_piece, state):
    model = "Sample text"
    view = line_edit.ViewLineView.from_piece(view_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == view_piece
    state = view.widget_state(widget)
    assert state
