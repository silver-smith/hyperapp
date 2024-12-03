from functools import partial
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .tested.code import ui_model_command


def _sample_fn_1(model, state, sample_service):
    return f'sample-fn-1: {state}, {sample_service}'


def _sample_fn_2(model, state, sample_service):
    return f'sample-fn-2: {state}, {sample_service}'


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        raw_fn=_sample_fn_1,
        bound_fn=partial(_sample_fn_1, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_model_command_1_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        raw_fn=_sample_fn_2,
        bound_fn=partial(_sample_fn_2, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_model_command_2_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    model_t = htypes.ui_model_command_tests.sample_model
    return {model_t: [command]}


@mark.fixture
def lcs(data_to_ref):
    command_3 = htypes.command.custom_ui_model_command(
        ui_command_d=data_to_ref(htypes.ui_model_command_tests.sample_command_3_d()),
        model_command_d=data_to_ref(htypes.ui_model_command_tests.sample_model_command_2_d()),
        layout=None,
        )
    command_list = htypes.command.custom_model_command_list(
        commands=(mosaic.put(command_3),)
        )
    lcs = Mock()
    lcs.get.return_value = command_list
    return lcs


def test_set_custom_ui_model_command(data_to_ref, custom_ui_model_commands, lcs):
    model_t = htypes.ui_model_command_tests.sample_model
    command = htypes.command.custom_ui_model_command(
        ui_command_d=data_to_ref(htypes.ui_model_command_tests.sample_command_2_d()),
        model_command_d=data_to_ref(htypes.ui_model_command_tests.sample_model_command_2_d()),
        layout=None,
        )
    custom_commands = custom_ui_model_commands(lcs, model_t)
    custom_commands.set(command)
    lcs.get.assert_called_once()
    lcs.set.assert_called_once()


def test_get_ui_model_commands(get_ui_model_commands, lcs):
    ctx = Context()
    model = htypes.ui_model_command_tests.sample_model()
    command_list = get_ui_model_commands(lcs, model, ctx)
    command_d_set = {
        command.d for command in command_list
        }
    assert command_d_set == {
        htypes.ui_model_command_tests.sample_model_command_1_d(),
        htypes.ui_model_command_tests.sample_model_command_2_d(),
        htypes.ui_model_command_tests.sample_command_3_d(),
        }, command_d_set
    for cmd in command_list:
        assert isinstance(cmd, ui_model_command.UnboundUiModelCommand)
