import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .fixtures import feed_fixtures
from .tested.code import record_field_adapter

log = logging.getLogger(__name__)


def _sample_record_fn(piece):
    log.info("Sample record fn: %s", piece)
    assert isinstance(piece, htypes.record_field_adapter_tests.sample_record), repr(piece)
    return htypes.record_field_adapter_tests.item(123, "Sample fn item")


def test_adapter(ui_adapter_creg):
    ctx = Context()
    model = htypes.record_field_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_field_adapter_tests.item)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_record_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    record_adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        system_fn=mosaic.put(system_fn),
        )
    adapter_piece = htypes.record_field_adapter.record_field_adapter(
        record_adapter=mosaic.put(record_adapter_piece),
        field_name='text',
        field_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
    adapter = record_field_adapter.RecordFieldAdapter.from_piece(adapter_piece, model, ctx)
    assert adapter.value == "Sample fn item"

    adapter.value_changed("New item")
    
    record_adapter = ui_adapter_creg.animate(record_adapter_piece, model, ctx)
    assert record_adapter.value.text == "New item"
