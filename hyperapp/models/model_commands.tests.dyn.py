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
from .tested.code import model_commands


def test_open_model_commands():
    model_state = htypes.model_commands_tests.sample_model_state()
    model_1 = htypes.model_commands_tests.sample_model_1()
    piece_1 = model_commands.open_model_commands(model_1, model_state)
    assert piece_1
    model_2 = htypes.model_commands_tests.sample_model_2()
    piece_2 = model_commands.open_model_commands(model_2, model_state)
    assert piece_2


def _sample_fn_1(model, state, sample_service):
    return f'sample-fn-1: {state}, {sample_service}'


def _sample_fn_2(model, sample_service):
    return f'sample-fn-2: {sample_service}'


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        unbound_fn=_sample_fn_1,
        bound_fn=partial(_sample_fn_1, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_command_1_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('model',),
        service_params=('sample_service',),
        unbound_fn=_sample_fn_2,
        bound_fn=partial(_sample_fn_2, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_command_2_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    model_t = htypes.model_commands_tests.sample_model_1
    return {model_t: [command]}


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Missing (empty) command list.
    return lcs


@mark.fixture
def piece():
    model = htypes.model_commands_tests.sample_model_1()
    model_state = htypes.model_commands_tests.sample_model_state()
    return htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )


def test_list_model_commands(lcs, piece):
    ctx = Context()
    item_list = model_commands.list_model_commands(piece, ctx, lcs)
    assert len(item_list) == 2
    assert sorted(item.name for item in item_list) == ['sample_command_1', 'sample_command_2']


async def test_run_command(data_to_ref, lcs, piece):
    navigator = Mock()
    current_item = htypes.model_commands.item(
        command_d=data_to_ref(htypes.ui_model_command_tests.sample_command_2_d()),
        name="<unused>",
        repr="<unused>",
        )
    ctx = Context(
        navigator=navigator,
        )
    result = await model_commands.run_command(piece, current_item, ctx, lcs)
    navigator.view.open.assert_called_once()
    assert navigator.view.open.call_args.args[1] == 'sample-fn-2: a-service'
