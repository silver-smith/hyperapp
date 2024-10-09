from unittest.mock import Mock

from . import htypes
from .services import mosaic
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import list


@mark.fixture
def adapter_piece():
    return htypes.list_adapter.static_list_adapter()


@mark.fixture
def piece(adapter_piece):
    return htypes.list.view(mosaic.put(adapter_piece))


def test_list(qapp, model_view_creg, piece):
    ctx = Context()
    model = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    state = None
    view = model_view_creg.animate(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert isinstance(state, htypes.list.state)
