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
from .code.selector import Selector
from .tested.code import crud

log = logging.getLogger(__name__)


def _sample_crud_get(piece, id):
    return htypes.crud_tests.sample_record(id, f'item#{id}')


def _sample_crud_update(piece, id, value):
    log.info("Update %s: #%d -> %s", piece, id, value)


@mark.fixture
def _sample_crud_get_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_crud_get),
        ctx_params=('piece', 'id'),
        service_params=(),
        )


@mark.fixture
def _sample_crud_update_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_crud_update),
        ctx_params=('piece', 'id', 'value'),
        service_params=(),
        )


@mark.fixture
def ctx():
    return Context()


def test_open_command_fn(_sample_crud_get_fn, _sample_crud_update_fn):
    value_t = htypes.crud_tests.sample_record
    piece = htypes.crud.open_command_fn(
        name='edit',
        value_t=pyobj_creg.actor_to_ref(value_t),
        key_field='id',
        init_action_fn=mosaic.put(_sample_crud_get_fn),
        commit_command_d=mosaic.put(htypes.crud.save_d()),
        commit_action_fn=mosaic.put(_sample_crud_update_fn),
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
def crud_model(model, _sample_crud_get_fn, _sample_crud_update_fn):
    value_t = htypes.crud_tests.sample_record
    return htypes.crud.model(
        value_t=pyobj_creg.actor_to_ref(value_t),
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action_fn=mosaic.put(_sample_crud_get_fn),
        commit_command_d=mosaic.put(htypes.crud.save_d()),
        commit_action_fn=mosaic.put(_sample_crud_update_fn),
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


def _sample_selector_get(value):
    return htypes.crud_tests.phony_view()


@mark.fixture
def _sample_selector_get_fn(partial_ref):
    return ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('value',),
        service_params=(),
        raw_fn=_sample_selector_get,
        bound_fn=_sample_selector_get,
        )


@mark.config_fixture('selector_reg')
def selector_reg_config(_sample_selector_get_fn):
    value_t = htypes.crud_tests.sample_selector
    get_fn = put_fn = None
    selector = Selector(
        get_fn=_sample_selector_get_fn,
        put_fn=None,
        )
    return {value_t: selector}


@mark.fixture
def selector_crud_model(model, _sample_crud_get_fn, _sample_crud_update_fn):
    value_t = htypes.crud_tests.sample_selector
    return htypes.crud.model(
        value_t=pyobj_creg.actor_to_ref(value_t),
        model=mosaic.put(model),
        key=mosaic.put(123),
        key_field='id',
        init_action_fn=mosaic.put(_sample_crud_get_fn),
        commit_command_d=mosaic.put(htypes.crud.save_d()),
        commit_action_fn=mosaic.put(_sample_crud_update_fn),
        )


def test_record_model_layout(crud_model, ctx):
    lcs = Mock()
    view_piece = crud.crud_model_layout(crud_model, lcs, ctx)
    assert isinstance(view_piece, htypes.form.view)


def test_selector_model_layout(selector_crud_model):
    lcs = Mock()
    ctx = Context(
        value=htypes.crud_tests.sample_selector(),
        )
    view_piece = crud.crud_model_layout(selector_crud_model, lcs, ctx)
    assert isinstance(view_piece, htypes.crud_tests.phony_view)


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
