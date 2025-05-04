from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .fixtures import qapp_fixtures, lcs_fixtures
from .tested.code import list


def sample_list_model(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_tests.sample_list), repr(piece)
    return [
        htypes.list_tests.item(11, "First item"),
        htypes.list_tests.item(22, "Second item"),
        htypes.list_tests.item(33, "Third item"),
        ]


@mark.fixture
def sample_list_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece',),
        service_params=(),
        raw_fn=sample_list_model,
        )


@mark.fixture
def adapter_piece():
    return htypes.list_adapter.static_list_adapter()


@mark.fixture
def piece(adapter_piece):
    return htypes.list.view(mosaic.put(adapter_piece))


def test_list(qapp, lcs, piece):
    ctx = Context()
    model = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    state = None
    view = list.ListView.from_piece(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert isinstance(state, htypes.list.state)


def test_index_list_ui_type_layout(sample_list_model_fn):
    piece = htypes.model.index_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.list_tests.item),
        )
    layout = list.index_list_ui_type_layout(piece, sample_list_model_fn)
    assert isinstance(layout, htypes.list.view)


def test_key_list_ui_type_layout(sample_list_model_fn):
    piece = htypes.model.key_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.list_tests.item),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        )
    layout = list.key_list_ui_type_layout(piece, sample_list_model_fn)
    assert isinstance(layout, htypes.list.view)
