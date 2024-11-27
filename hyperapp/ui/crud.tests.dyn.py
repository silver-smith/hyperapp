from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .tested.code import crud


def _sample_get(piece, id):
    return htypes.crud_tests.sample_record(id, f'item#{id}')


@mark.fixture
def _sample_get_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_get),
        ctx_params=('piece', 'id'),
        service_params=(),
        )


def test_open_command_fn(_sample_get_fn):
    record_t = htypes.crud_tests.sample_record
    piece = htypes.crud.open_command_fn(
        name='edit',
        record_t=pyobj_creg.actor_to_ref(record_t),
        key_field='id',
        init_action_fn=mosaic.put(_sample_get_fn),
        commit_action='update',
        )
    fn = crud.CrudOpenFn.from_piece(piece)

    assert fn.missing_params(Context()) == {'model', 'current_item'}
    ctx = Context(
        model=htypes.crud_tests.sample_model(),
        current_item=htypes.crud_tests.sample_item(id=123),
        )
    assert not fn.missing_params(ctx)
    crud_model = fn.call(ctx)
    assert isinstance(crud_model, htypes.crud.model)


def test_init_fn(_sample_get_fn):
    piece = htypes.crud.init_fn()
    fn = crud.CrudInitFn.from_piece(piece)

    record_t = htypes.crud_tests.sample_record
    model = htypes.crud_tests.sample_model()
    crud_model = htypes.crud.model(
        record_t=pyobj_creg.actor_to_ref(record_t),
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action_fn=mosaic.put(_sample_get_fn),
        commit_action='update',
        )
    assert fn.missing_params(Context()) == {'model'}
    ctx = Context(
        model=crud_model,
        )
    assert not fn.missing_params(ctx)
    result = fn.call(ctx)
    assert result == htypes.crud_tests.sample_record(123, 'item#123')


def test_model_layout(_sample_get_fn):
    model = htypes.crud_tests.sample_model()
    record_t = htypes.crud_tests.sample_record
    piece = htypes.crud.model(
        record_t=pyobj_creg.actor_to_ref(record_t),
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action_fn=mosaic.put(_sample_get_fn),
        commit_action='update',
        )
    result = crud.crud_model_layout(piece)
    assert isinstance(result, htypes.form.view)
