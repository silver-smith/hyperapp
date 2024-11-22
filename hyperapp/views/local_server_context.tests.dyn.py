from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import local_server_context


@mark.service
def local_server_peer():
    return None


def test_local_server_context_view(qapp):
    ctx = Context()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.local_server_context.view(
        base=mosaic.put(base_piece),
        )
    base_state = htypes.label.state()
    state = htypes.local_server_context.state(
        base=mosaic.put(base_state),
        )
    view = local_server_context.LocalServerContextView.from_piece(piece, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == piece
    state = view.widget_state(widget)
    assert state


def test_open_local_server_context(view_creg):
    ctx = Context()
    piece = htypes.label.view("Sample label")
    state = htypes.label.state()
    view = view_creg.animate(piece, ctx)
    hook = Mock()
    result = local_server_context.open_local_server_context(view, state, hook, ctx)
