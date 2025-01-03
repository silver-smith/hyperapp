import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .tested.code import crud

log = logging.getLogger(__name__)


def _sample_get(piece, id):
    return htypes.crud_tests.sample_record(id, f'item#{id}')


def _sample_update(piece, id, value):
    log.info("Update %s: #%d -> %s", piece, id, value)


@mark.fixture
def _sample_get_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_get),
        ctx_params=('piece', 'id'),
        service_params=(),
        )


@mark.fixture
def _sample_update_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_update),
        ctx_params=('piece', 'id', 'value'),
        service_params=(),
        )


@mark.fixture
def ctx():
    return Context()


def test_open_command_fn(_sample_get_fn, _sample_update_fn):
    value_t = htypes.crud_tests.sample_record
    piece = htypes.crud.open_command_fn(
        name='edit',
        value_t=pyobj_creg.actor_to_ref(value_t),
        key_field='id',
        init_action_fn=mosaic.put(_sample_get_fn),
        commit_command_d=mosaic.put(htypes.crud.save_d()),
        commit_action_fn=mosaic.put(_sample_update_fn),
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


@mark.fixture
def model():
    return htypes.crud_tests.sample_model()


@mark.fixture
def crud_model(model, _sample_get_fn, _sample_update_fn):
    value_t = htypes.crud_tests.sample_record
    return htypes.crud.model(
        value_t=pyobj_creg.actor_to_ref(value_t),
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action_fn=mosaic.put(_sample_get_fn),
        commit_command_d=mosaic.put(htypes.crud.save_d()),
        commit_action_fn=mosaic.put(_sample_update_fn),
        )


def test_init_fn(crud_model):
    piece = htypes.crud.init_fn()
    fn = crud.CrudInitFn.from_piece(piece)

    assert fn.missing_params(Context()) == {'model'}
    ctx = Context(
        model=crud_model,
        )
    assert not fn.missing_params(ctx)
    result = fn.call(ctx)
    assert result == htypes.crud_tests.sample_record(123, 'item#123')


def test_model_layout(crud_model, ctx):
    lcs = Mock()
    result = crud.crud_model_layout(crud_model, lcs, ctx)
    assert isinstance(result, htypes.form.view)


async def test_model_commands(crud_model):
    commands = crud.crud_model_commands(crud_model)
    assert commands
    [unbound_cmd] = commands
    assert unbound_cmd.properties
    value = {'text': "Some text"}
    input = Mock()
    input.get_value.return_value = value
    ctx = Context(
        model=crud_model,
        piece=crud_model,
        input=input,
        )
    bound_cmd = unbound_cmd.bind(ctx)
    await bound_cmd.run()
