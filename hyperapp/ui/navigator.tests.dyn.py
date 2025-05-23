from unittest.mock import MagicMock, Mock

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
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
    label = htypes.label.view("Sample label")
    prev_rec = htypes.navigator.history_rec(
        view=mosaic.put(label),
        model=mosaic.put(model),
        state=mosaic.put(htypes.label.state()),
        layout_k=None,
        prev=None,
        next=None,
        )
    next_rec = htypes.navigator.history_rec(
        view=mosaic.put(label),
        model=mosaic.put(model),
        state=mosaic.put(htypes.label.state()),
        layout_k=None,
        prev=None,
        next=None,
        )
    model_t = deduce_t(model)
    layout_k = htypes.ui.model_layout_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        )
    return htypes.navigator.view(
        current_view=mosaic.put(label),
        current_model=mosaic.put(model),
        layout_k=mosaic.put(layout_k),
        prev=mosaic.put(prev_rec),
        next=mosaic.put(next_rec),
        )


@mark.fixture
def state():
    return htypes.label.state()


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
    assert state == htypes.label.state()


@mark.fixture.obj
def model_layout_reg():
    return MagicMock()


async def test_open_with_default_model_layout(view_reg, qapp, model, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    label = htypes.label.view("Sample label")
    new_child_view = view_reg.animate(label, ctx)
    new_child_widget = new_child_view.construct_widget(None, ctx)
    await view.open(ctx, model, new_child_view, new_child_widget)


async def test_set_layout(view_reg, model_layout_reg, qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    label = htypes.label.view("Another sample label")
    new_child_view = view_reg.animate(label, ctx)
    new_child_widget = new_child_view.construct_widget(None, ctx)
    view.replace_child(ctx, widget, 0, new_child_view, new_child_widget)
    rctx = Context()
    await view.children_changed(ctx, rctx, new_child_widget, save_layout=True)
    model_layout_reg.__setitem__.assert_called_once()
    assert isinstance(model_layout_reg.__setitem__.call_args.args[0], htypes.ui.model_layout_k)


def test_go_back_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_back(view, widget, ctx)


def test_go_forward_command(qapp, state, ctx, view):
    widget = view.construct_widget(state, ctx)
    navigator.go_forward(view, widget, ctx)
