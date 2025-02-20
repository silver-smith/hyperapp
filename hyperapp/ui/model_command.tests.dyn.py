from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import model_command


def _sample_fn(model, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


def test_model_command_from_piece():
    d = htypes.model_command_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('model', 'state'),
        service_params=('sample_service',),
        )
    piece = htypes.command.model_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )
    command = model_command.model_command_from_piece(piece)
    assert isinstance(command, model_command.UnboundModelCommand)


def test_model_command_enumerator_from_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('model', 'state'),
        service_params=('sample_service',),
        )
    piece = htypes.command.model_command_enumerator(
        system_fn=mosaic.put(system_fn),
        )
    command = model_command.model_command_enumerator_from_piece(piece)
    assert isinstance(command, model_command.UnboundModelCommandEnumerator)


def test_global_command_reg(global_model_command_reg):
    commands = global_model_command_reg()
    # assert commands


def test_model_command_reg(model_command_reg):
    model_t = htypes.model_command_tests.sample_model
    commands = model_command_reg(model_t)


def test_model_command_enumerator_reg(model_command_enumerator_reg):
    model_t = htypes.model_command_tests.sample_model
    commands = model_command_enumerator_reg(model_t)


def test_get_model_commands(get_model_commands):
    ctx = Context()
    model_t = htypes.model_command_tests.sample_model
    commands = get_model_commands(model_t, ctx)
