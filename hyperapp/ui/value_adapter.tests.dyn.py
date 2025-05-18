from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import value_adapter


@mark.fixture
def ctx():
    return Context()


def test_value_adapter(ctx):
    model = 123
    accessor = htypes.accessor.model_accessor()
    cvt = htypes.type_convertor.int_to_string_convertor()
    piece = htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )
    adapter = value_adapter.ValueAdapter.from_piece(piece, model, ctx)
    assert adapter.get_value() == '123'
