from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import crud


def test_open():
    piece = htypes.crud.crud_open_command_fn(
        name='edit',
        key_field='id',
        init_action='get',
        commit_action='update',
        )
    ctx = Context(
        model=htypes.crud_tests.sample_model(),
        current_item=htypes.crud_tests.sample_item(id=123),
        )
    fn = crud.CrudOpenFn.from_piece(piece)
    assert not fn.missing_params(ctx)
    assert fn.missing_params(Context()) == {'model', 'current_item'}
    crud_model = fn.call(ctx)
    assert isinstance(crud_model, htypes.crud.model)


@mark.config_fixture('crud_action_reg')
def action_reg_config():
    return {
        (htypes.crud_tests.sample_model, 'get'): 'sample action',
        }


def test_action_reg(crud_action_reg):
    model_t = htypes.crud_tests.sample_model
    action = crud_action_reg(model_t, 'get')
    assert action == 'sample action'


def test_model_layout():
    model = htypes.crud_tests.sample_model()
    piece = htypes.crud.model(
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action='get',
        commit_action='update',
        )
    crud.crud_model_layout(piece)
