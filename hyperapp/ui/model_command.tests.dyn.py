from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.command_enumerator import UnboundCommandEnumerator
from .tested.code import model_command


def _sample_command(piece, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


def _sample_model(piece, sample_service):
    return [
        htypes.model_command_tests.sample_item(
            id=str(idx),
            value=idx*100,
            )
        for idx in range(10)
        ]


def _sample_add_command(piece, state, sample_service):
    return '5'


def _sample_remove_command(piece, current_key, sample_service):
    return True


@mark.fixture
def sample_command_fn():
    return htypes.command.model_command_fn(
        function=pyobj_creg.actor_to_ref(_sample_command),
        ctx_params=('piece', 'state'),
        service_params=('sample_service',),
        )


@mark.fixture
def sample_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_model),
        ctx_params=('piece',),
        service_params=('sample_service',),
        )


def _sample_command_enum(piece, state, sample_service):
    return []


@mark.fixture
def sample_command_enum_fn():
    return htypes.command.model_command_enum_fn(
        function=pyobj_creg.actor_to_ref(_sample_command_enum),
        ctx_params=('piece', 'state'),
        service_params=('sample_service',),
        )


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture
def model():
    return htypes.model_command_tests.sample_model()


@mark.fixture
def ctx(generate_rsa_identity, model):
    identity = generate_rsa_identity(fast=True)
    return Context(
        identity=identity,
        model=model,
        piece=model,
        )


async def test_command_fn(model, ctx, sample_command_fn):
    fn = model_command.ModelCommandFn.from_piece(sample_command_fn)
    assert fn.piece == sample_command_fn
    result = await fn.call(ctx, piece=model, state="Sample state")
    assert isinstance(result, htypes.command.command_result)
    assert result.diff is None


@mark.fixture.obj
def model_servant_set(system_fn_creg, model_servant, sample_model_fn, model):
    model_servant(model).set_servant_fn(
        key_field='id',
        key_field_t=htypes.builtin.string,
        fn=system_fn_creg.animate(sample_model_fn),
        )


@mark.fixture
def remote_identity(generate_rsa_identity):
    return generate_rsa_identity(fast=True)


@mark.fixture
def rpc_system_call_factory(remote_identity, receiver_peer, sender_identity, fn):
    request = Mock(receiver_identity=remote_identity)
    def call(**kw):
        ctx = Context(**kw, request=request)
        return fn.call(ctx)
    return call


@mark.fixture
async def run_comand_add_fn_test(diff_creg, model_servant_set, model, ctx, remote_peer):
    piece = htypes.command.model_command_add_fn(
        function=pyobj_creg.actor_to_ref(_sample_add_command),
        ctx_params=('piece', 'state'),
        service_params=('sample_service',),
        )
    fn = model_command.ModelCommandAddFn.from_piece(piece)
    assert fn.piece == piece
    result = await fn.call(ctx, remote_peer, state="Sample state")
    assert isinstance(result, htypes.command.command_result)
    model_diff = web.summon(result.diff)
    diff = diff_creg.invite(model_diff.diff)
    diff_model = web.summon(model_diff.model)
    if remote_peer:
        assert web.summon(diff_model.remote_peer) == remote_peer.piece
        assert web.summon(diff_model.model) == model
    else:
        assert diff_model == model
    assert diff.item.id == '5'
    assert web.summon_opt(result.key) == '5'
    assert result.model is None


async def test_command_add_fn_locally(run_comand_add_fn_test):
    await run_comand_add_fn_test(remote_peer=None)


async def test_command_add_fn_remotelly(remote_identity, run_comand_add_fn_test):
    await run_comand_add_fn_test(remote_peer=remote_identity.peer)


async def test_command_remove_fn(diff_creg, model_servant_set, model, ctx):
    piece = htypes.command.model_command_remove_fn(
        function=pyobj_creg.actor_to_ref(_sample_remove_command),
        ctx_params=('piece', 'current_key'),
        service_params=('sample_service',),
        )
    fn = model_command.ModelCommandRemoveFn.from_piece(piece)
    assert fn.piece == piece
    result = await fn.call(ctx, current_key='5')
    assert isinstance(result, htypes.command.command_result)
    model_diff = web.summon(result.diff)
    diff = diff_creg.invite(model_diff.diff)
    assert web.summon(model_diff.model) == model
    assert diff.key == '5'
    assert result.model is None
    assert result.key is None



def test_command_enum_fn(model, ctx, sample_command_enum_fn):
    enum = model_command.ModelCommandEnumFn.from_piece(sample_command_enum_fn)
    assert enum.piece == sample_command_enum_fn
    result = enum.call(ctx, piece=model, state="Sample state")
    assert type(result) is tuple


def test_model_command_from_piece(sample_command_fn):
    d = htypes.model_command_tests.sample_command_d()
    piece = htypes.command.model_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(sample_command_fn),
        )
    command = model_command.model_command_from_piece(piece)
    assert isinstance(command, model_command.UnboundModelCommand)
    assert command.piece == piece


def test_model_command_enumerator_from_piece(sample_command_fn):
    piece = htypes.command.model_command_enumerator(
        system_fn=mosaic.put(sample_command_fn),
        )
    command = model_command.model_command_enumerator_from_piece(piece)
    assert isinstance(command, UnboundCommandEnumerator)


def test_global_command_reg(global_model_command_reg):
    commands = global_model_command_reg()
    # assert commands


def test_model_command_reg(model_command_reg):
    model_t = htypes.model_command_tests.sample_model
    commands = model_command_reg(model_t)


def test_model_command_enumerator_reg(model_command_enumerator_reg):
    model_t = htypes.model_command_tests.sample_model
    commands = model_command_enumerator_reg(model_t)


def test_get_model_commands(ctx, get_model_commands):
    model_t = htypes.model_command_tests.sample_model
    commands = get_model_commands(model_t, ctx)
