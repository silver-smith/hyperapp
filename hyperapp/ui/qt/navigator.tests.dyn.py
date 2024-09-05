from unittest.mock import Mock

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


@mark.fixture
def piece():
    adapter_piece = htypes.str_adapter.static_str_adapter()
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    prev_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put("Sample piece"),
        state=mosaic.put(htypes.text.state()),
        prev=None,
        next=None,
        )
    next_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put("Sample piece"),
        state=mosaic.put(htypes.text.state()),
        prev=None,
        next=None,
        )
    return htypes.navigator.view(
        current_view=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        prev=mosaic.put(prev_rec),
        next=mosaic.put(next_rec),
        )


@mark.fixture
def state():
    return htypes.text.state()


@mark.fixture
def ctx():
    return Context(lcs=None)


@mark.fixture
def view(piece, ctx):
    view = navigator.NavigatorView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    return view


def test_widget(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    assert view.piece
    assert view.widget_state(widget) == htypes.text.state()


def test_go_back_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_back(view, state, widget)


def test_go_forward_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_forward(view, state, widget)
