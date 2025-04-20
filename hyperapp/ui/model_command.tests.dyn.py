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
    return "Sample model"


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        piece=model,
        )


async def test_command_fn(model, ctx, sample_command_fn):
    fn = model_command.ModelCommandFn.from_piece(sample_command_fn)
    assert fn.piece == sample_command_fn
    result = await fn.call(ctx, piece=model, state="Sample state")
    assert isinstance(result, htypes.command.command_result)


async def test_command_add_fn(system_fn_creg, diff_creg, model_servant, sample_model_fn, model, ctx):
    model_servant(model).set_servant_fn(
        key_field='id',
        key_field_t=htypes.builtin.string,
        fn=system_fn_creg.animate(sample_model_fn),
        )
    piece = htypes.command.model_command_add_fn(
        function=pyobj_creg.actor_to_ref(_sample_add_command),
        ctx_params=('piece', 'state'),
        service_params=('sample_service',),
        )
    fn = model_command.ModelCommandAddFn.from_piece(piece)
    assert fn.piece == piece
    result = await fn.call(ctx, piece=model, state="Sample state")
    assert isinstance(result, htypes.command.command_result)
    diff = diff_creg.invite(result.diff)
    assert diff.item.id == '5'
    assert web.summon(result.key) == '5'


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
