import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .fixtures import feed_fixtures
from .tested.code import record_adapter

log = logging.getLogger(__name__)


@mark.fixture
def ctx():
    return Context()


def test_static_adapter(ctx):
    model = htypes.record_adapter_tests.item(123, "Sample static item")
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.static_record_adapter(
        record_t=mosaic.put(record_t_res),
        )
    adapter = record_adapter.StaticRecordAdapter.from_piece(adapter_piece, model, ctx)
    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample static item"


def _sample_record_model(piece):
    log.info("Sample record fn: %s", piece)
    assert isinstance(piece, htypes.record_adapter_tests.sample_record), repr(piece)
    return htypes.record_adapter_tests.item(123, "Sample fn item")


@mark.fixture
def sample_record_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece',),
        service_params=(),
        raw_fn=_sample_record_model,
        )


def test_fn_adapter(ctx, sample_record_model_fn):
    model = htypes.record_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        system_fn=mosaic.put(sample_record_model_fn.piece),
        )
    adapter = record_adapter.FnRecordAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample fn item"
