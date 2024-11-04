from functools import partial
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .tested.code import global_commands


def test_open_global_commands():
    piece = global_commands.open_global_commands()
    assert piece


def _sample_fn(sample_service):
    return f'sample-fn: {sample_service}'


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=('sample_service',),
        unbound_fn=_sample_fn,
        bound_fn=partial(_sample_fn, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=htypes.global_commands_tests.sample_command_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Missing (empty) command list.
    return lcs


@mark.fixture
def piece():
    return htypes.global_commands.view()


def test_list_global_commands(lcs, piece):
    ctx = Context()
    item_list = global_commands.list_global_commands(piece, lcs)
    assert 'sample_command' in [item.name for item in item_list]


async def test_run_command(data_to_ref, lcs, piece):
    navigator = Mock()
    current_item = htypes.global_commands.item(
        ui_command_d=data_to_ref(htypes.global_commands_tests.sample_command_d()),
        model_command_d=data_to_ref(htypes.global_commands_tests.sample_model_command_d()),
        name="<unused>",
        groups="<unused>",
        repr="<unused>",
        )
    ctx = Context(
        navigator=navigator,
        )
    result = await global_commands.run_command(piece, current_item, lcs, ctx)
    navigator.view.open.assert_called_once()
    assert navigator.view.open.call_args.args[1] == 'sample-fn: a-service'
