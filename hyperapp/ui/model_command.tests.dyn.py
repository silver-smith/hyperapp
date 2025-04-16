from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.command_enumerator import UnboundCommandEnumerator
from .tested.code import model_command


def _sample_command(model, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_command_fn():
    return htypes.command.model_command_fn(
        function=pyobj_creg.actor_to_ref(_sample_command),
        ctx_params=('model', 'state'),
        service_params=('sample_service',),
        )


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture
def ctx():
    return Context()


def test_command_fn(ctx, sample_command_fn):
    fn = model_command.ModelCommandFn.from_piece(sample_command_fn)
    assert fn.piece == sample_command_fn
    result = fn.call(ctx, model="Sample model", state="Sample state")
    assert isinstance(result, htypes.command.remote_command_result)


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
