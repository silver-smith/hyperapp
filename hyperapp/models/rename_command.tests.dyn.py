from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .tested.code import rename_command


def _sample_fn(model, state):
    return f'sample-fn: {state}'


@mark.config_fixture('model_command_reg')
def model_command_reg_config(rpc_system_call_factory):
    system_fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory, 
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    command = UnboundModelCommand(
        d=htypes.rename_command_tests.sample_command_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    model_t = htypes.rename_command_tests.sample_model
    return {model_t: [command]}


@mark.fixture
def piece():
    model = htypes.rename_command_tests.sample_model()
    model_state = htypes.rename_command_tests.sample_model_state()
    return htypes.model_commands.model(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )


@mark.fixture
def d_ref():
    d = htypes.rename_command_tests.sample_command_d()
    return mosaic.put(d)


def test_rename_to(piece, d_ref):
    form = rename_command.model_command_rename_to(piece, d_ref)
    assert form.name == 'sample_command'


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Missing (empty) command list.
    return lcs


def test_rename(lcs, piece, d_ref):
    ctx = Context()
    form = htypes.rename_command.form(
        name='new_name',
        )
    rename_command.model_command_rename(piece, d_ref, form, lcs, ctx)
    lcs.set.assert_called_once()
