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


def test_view(qapp, model):
    ctx = Context()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.arg_mark.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
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
