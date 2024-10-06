from unittest.mock import Mock

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures, feed_fixtures
from .tested.code import form


def _sample_form_fn(piece):
    assert isinstance(piece, htypes.form_tests.sample_form), repr(piece)
    return htypes.form_tests.item(123, "Sample  item")


@mark.fixture
def adapter_piece():
    item_t_res = pyobj_creg.actor_to_piece(htypes.form_tests.item)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_form_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    return htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(item_t_res),
        system_fn=mosaic.put(system_fn),
        )


@mark.fixture
def piece(adapter_piece):
    return htypes.form.view(mosaic.put(adapter_piece))


@mark.fixture
def lcs():
    lcs = Mock()
    # Fall thru to default layout.
    lcs.get.return_value = None
    return lcs


def test_form(qapp, lcs, piece):
    ctx = Context(lcs=lcs)
    model = htypes.form_tests.sample_form()
    state = None
    view = form.FormView.from_piece(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state
    assert hash(state)  # Check it is hashable.
