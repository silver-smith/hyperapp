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
from .tested.code import command_list_model, global_commands


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
        raw_fn=_sample_fn,
        bound_fn=partial(_sample_fn, sample_service='a-service'),
        )
    properties = htypes.command.properties(
        is_global=True,
        uses_state=False,
        remotable=False,
        )
    command = UnboundModelCommand(
        d=htypes.global_commands_tests.sample_command_d(),
        ctx_fn=system_fn,
        properties=properties,
        )
    return [command]


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Missing (empty) command list.
    return lcs


@mark.fixture
def piece():
    return htypes.global_commands.model()


def test_list_global_commands(lcs, piece):
    ctx = Context()
    item_list = global_commands.list_global_commands(piece, lcs)
    assert 'sample_command' in [item.name for item in item_list]


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
        ui_command_d=mosaic.put(htypes.global_commands_tests.sample_command_d()),
        model_command_d=mosaic.put(htypes.global_commands_tests.sample_model_command_d()),
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
    result = await global_commands.run_command(piece, current_item, lcs, ctx.push())
    navigator.view.open.assert_called_once()
    assert navigator.view.open.call_args.args[1] == 'sample-fn: a-service'


def test_selector_get(piece):
    d = htypes.global_commands_tests.sample_model_command_d()
    value = htypes.global_commands.command_arg(
        d=mosaic.put(d),
        )
    model = global_commands.global_command_get(value)
    assert model == piece


def test_selector_pick(piece):
    current_item = htypes.command_list_model.item(
        ui_command_d=mosaic.put(htypes.global_commands_tests.sample_command_d()),
        model_command_d=mosaic.put(htypes.global_commands_tests.sample_model_command_d()),
        name="<unused>",
        groups="<unused>",
        repr="<unused>",
        shortcut="<unused>",
        text="<unused>",
        tooltip="<unused>",
        )
    value = global_commands.global_command_pick(piece, current_item)
    value == htypes.global_commands.command_arg(
        d=mosaic.put(htypes.global_commands_tests.sample_model_command_d()),
        )


def test_format_model(piece):
    title = global_commands.format_model(piece)
    assert type(title) is str
