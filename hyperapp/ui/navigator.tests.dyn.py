from unittest.mock import MagicMock, Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import navigator


def _wrapper(diff):
    return diff


@mark.fixture.obj
def model():
    return "Sample piece"


@mark.fixture
def piece(model):
    adapter_piece = htypes.str_adapter.static_str_adapter()
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    prev_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put(model),
        state=mosaic.put(htypes.text.state('')),
        layout_k=None,
        prev=None,
        next=None,
        )
    next_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put(model),
        state=mosaic.put(htypes.text.state('')),
        layout_k=None,
        prev=None,
        next=None,
        )
    return htypes.navigator.view(
        current_view=mosaic.put(text_piece),
        current_model=mosaic.put(model),
        layout_k=None,
        prev=mosaic.put(prev_rec),
        next=mosaic.put(next_rec),
        )


@mark.fixture
def state():
    return htypes.text.state('')


@mark.fixture
def ctx(model):
    return Context().push(
        model=model,
        )


@mark.fixture
def view(piece, ctx):
    view = navigator.NavigatorView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    return view


def test_widget(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state == htypes.text.state("Sample piece")


@mark.fixture.obj
def model_layout_reg():
    return MagicMock()


def test_set_layout(view_reg, model_layout_reg, qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    adapter_piece = htypes.str_adapter.static_str_adapter()
    text_piece = htypes.text.edit_view(mosaic.put(adapter_piece))
    new_child_view = view_reg.animate(text_piece, ctx)
    new_child_widget = new_child_view.construct_widget(None, ctx)
    view.replace_child(ctx, widget, 0, new_child_view, new_child_widget)
    model_layout_reg.__setitem__.assert_called_once()
    assert isinstance(model_layout_reg.__setitem__.call_args.args[0], htypes.ui.model_layout_k)


def test_go_back_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_back(view, widget, ctx)


def test_go_forward_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_forward(view, widget, ctx)
