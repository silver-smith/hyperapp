from unittest.mock import Mock

from . import htypes
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import context_view


def test_local_server_context_view(qapp, view_reg):
    ctx = Context()
    base_piece = htypes.label.view("Sample label")
    base_view = view_reg.animate(base_piece, ctx)
    view = context_view.ContextView(base_view, label="Sample view")
    state = None
    widget = view.construct_widget(state, ctx)
    state = view.widget_state(widget)
    assert state
