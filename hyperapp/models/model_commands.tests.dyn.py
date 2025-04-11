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
from .tested.code import command_list_model, model_commands


def test_open_model_commands():
    model_state = htypes.model_commands_tests.sample_model_state()
    model_1 = htypes.model_commands_tests.sample_model_1()
    piece_1 = model_commands.open_model_commands(model_1, model_state)
    assert piece_1


def _sample_fn_1(model, sample_service):
    return f'sample-fn-1: {sample_service}'


def _sample_fn_2(model, sample_service):
    return f'sample-fn-2: {sample_service}'


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    system_fn_1 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('model',),
        service_params=('sample_service',),
        raw_fn=_sample_fn_1,
        bound_fn=partial(_sample_fn_1, sample_service='a-service'),
        )
    command_1 = UnboundModelCommand(
        d=htypes.model_commands_tests.sample_command_1_d(),
        ctx_fn=system_fn_1,
        properties=htypes.command.properties(False, False, False),
        )
    system_fn_2 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('model',),
        service_params=('sample_service',),
        raw_fn=_sample_fn_2,
        bound_fn=partial(_sample_fn_2, sample_service='a-service'),
        )
    command_2 = UnboundModelCommand(
        d=htypes.model_commands_tests.sample_command_2_d(),
        ctx_fn=system_fn_2,
        properties=htypes.command.properties(False, False, False),
        )
    return {
        htypes.model_commands_tests.sample_model_1: [command_1],
        htypes.model_commands_tests.sample_model_2: [command_2],
        }


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Missing (empty) command list.
    return lcs


@mark.fixture
def piece():
    model = htypes.model_commands_tests.sample_model_2()
    model_state = htypes.model_commands_tests.sample_model_state()
    return htypes.model_commands.model(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )


def test_list_model_commands(lcs, piece):
    ctx = Context()
    item_list = model_commands.list_model_commands(piece, ctx, lcs)
    assert 'Sample command 2' in [item.name for item in item_list]


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config():
    def k(t):
        return htypes.ui.model_layout_k(pyobj_creg.actor_to_ref(t))
    return {
        k(htypes.builtin.string): htypes.text.edit_view(
            adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
            ),
        }


async def test_run_command(lcs, piece):
    navigator = Mock()
    current_item = htypes.command_list_model.item(
        ui_command_d=mosaic.put(htypes.model_commands_tests.sample_command_2_d()),
        model_command_d=mosaic.put(htypes.model_commands_tests.sample_model_command_2_d()),
        name="<unused>",
        groups="<unused>",
        repr="<unused>",
        shortcut="",
        text="",
        tooltip="",
        )
    ctx = Context(
        navigator=navigator,
        )
    result = await model_commands.run_command(piece, current_item, ctx, lcs)
    navigator.view.open.assert_called_once()
    assert navigator.view.open.call_args.args[1] == 'sample-fn-2: a-service'


def test_format_model(piece):
    title = model_commands.format_model(piece)
    assert type(title) is str
