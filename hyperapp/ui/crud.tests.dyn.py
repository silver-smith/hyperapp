from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
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


def _sample_get(piece, id):
    return htypes.crud_tests.sample_record(id, f'item#{id}')


@mark.fixture
def _sample_get_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_get),
        ctx_params=('piece', 'id'),
        service_params=(),
        )

    
@mark.config_fixture('crud_action_reg')
def action_reg_config(_sample_get_fn):
    return {
        (htypes.crud_tests.sample_model, 'get'): _sample_get_fn
        }


def test_action_reg(crud_action_reg, _sample_get_fn):
    model_t = htypes.crud_tests.sample_model
    action = crud_action_reg(model_t, 'get')
    assert isinstance(action, ContextFn)
    assert action.piece == _sample_get_fn


def test_model_layout():
    model = htypes.crud_tests.sample_model()
    piece = htypes.crud.model(
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action='get',
        commit_action='update',
        )
    ctx = Context()
    result = crud.crud_model_layout(piece, ctx)
    assert isinstance(result, htypes.crud_tests.sample_record)
    assert result.id == 123
