from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import model_field_wrapper_view


@mark.fixture
def model():
    return htypes.model_field_wrapper_view_tests.sample_model(
        some_field='Some value',
        )


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


def test_view(ctx):
    base = htypes.label.view("Sample label")
    piece = htypes.model_field_wrapper_view.view(
        base_view=mosaic.put(base),
        field_name='some_field',
        )
    view = model_field_wrapper_view.ModelFieldWrapperView.from_piece(piece, ctx)
    assert view.piece == piece
    assert view.children_context(ctx).model == 'Some value'
