from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import arg_mark


@mark.fixture
def model():
    return htypes.arg_mark_tests.sample_model()


@mark.fixture
def value():
    return htypes.arg_mark_tests.sample_value()


def test_view(qapp, model, value):
    ctx = Context()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.arg_mark.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
        value=mosaic.put(value),
        )
    base_state = htypes.label.state()
    state = htypes.context_view.state(
        base=mosaic.put(base_state),
        )
    view = arg_mark.MarkView.from_piece(piece, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == piece
    state = view.widget_state(widget)
    assert state
    children_ctx = view.children_context(ctx)
    assert children_ctx


def test_add_mark(view_reg, model):
    ctx = Context()
    label_view = htypes.label.view("Sample label")
    state = htypes.label.state()
    navigator_piece = htypes.navigator.view(
        current_view=mosaic.put(label_view),
        current_model=mosaic.put(model),
        layout_k=None,
        prev=None,
        next=None,
        )
    navigator = view_reg.animate(navigator_piece, ctx)
    hook = Mock()
    result = arg_mark.add_mark(navigator, state, hook, model, ctx)
    hook.replace_view.assert_called_once()


def test_remove_mark(view_reg, model, value):
    ctx = Context()
    label_view = htypes.label.view("Sample label")
    label_state = htypes.label.state()
    view_piece = htypes.arg_mark.view(
        base=mosaic.put(label_view),
        model=mosaic.put(model),
        value=mosaic.put(value),
        )
    state = htypes.context_view.state(
        base=mosaic.put(label_state),
        )
    view = view_reg.animate(view_piece, ctx)
    hook = Mock()
    result = arg_mark.remove_mark(view, state, hook, ctx)
    hook.replace_view.assert_called_once()
