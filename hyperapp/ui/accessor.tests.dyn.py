from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import accessor


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def model():
    return htypes.accessor_tests.sample_model(
        id=123,
        value='A value',
        )


def test_model_accessor(ctx, model):
    piece = htypes.accessor.model_accessor()
    acc = accessor.ModelAccessor.from_piece(piece, model, ctx)
    assert acc.get_value() == model



@mark.fixture.obj
def sample_record_adapter(model):
    adapter = Mock()
    adapter.get_value.return_value = model
    from_piece = Mock(return_value=adapter)
    return from_piece


@mark.config_fixture('ui_adapter_creg')
def ui_adapter_creg_config(sample_record_adapter):
    return {
        htypes.accessor_tests.sample_record_adapter: sample_record_adapter,
        }


def test_record_field_accessor(ctx, model, sample_record_adapter):
    record_adapter = htypes.accessor_tests.sample_record_adapter()
    piece = htypes.accessor.record_field_accessor(
        record_adapter=mosaic.put(record_adapter),
        field_name='value',
        )
    acc = accessor.RecordFieldAccessor.from_piece(piece, model, ctx)
    assert acc.get_value() == model.value
