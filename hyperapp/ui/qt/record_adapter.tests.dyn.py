import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .fixtures import feed_fixtures
from .tested.code import record_adapter

log = logging.getLogger(__name__)


def _sample_record_fn(piece):
    log.info("Sample record fn: %s", piece)
    assert isinstance(piece, htypes.record_adapter_tests.sample_record), repr(piece)
    return htypes.record_adapter_tests.item(123, "Sample item")


def test_fn_adapter():
    ctx = Context()
    model = htypes.record_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_record_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        system_fn=mosaic.put(system_fn),
        )
    adapter = record_adapter.FnRecordAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample item"
