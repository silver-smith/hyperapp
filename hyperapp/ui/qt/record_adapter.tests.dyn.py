import asyncio
import logging
from functools import partial

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .tested.code import record_adapter

log = logging.getLogger(__name__)


def sample_record_fn(piece):
    log.info("Sample record fn: %s", piece)
    assert isinstance(piece, htypes.record_adapter_tests.sample_record), repr(piece)
    return htypes.record_adapter_tests.item(123, "Sample item")


def test_fn_adapter():
    ctx = Context()
    model = htypes.record_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        function=fn_to_ref(sample_record_fn),
        params=('piece',),
        )
    adapter = record_adapter.FnRecordAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample item"
