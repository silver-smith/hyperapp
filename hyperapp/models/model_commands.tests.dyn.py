from functools import partial
from unittest.mock import Mock, AsyncMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.model_command import ModelCommandFn, UnboundModelCommand
from .fixtures import visualizer_fixtures
from .tested.code import command_list_model, model_commands


@mark.fixture
def ctx():
    return Context()


def test_open_model_commands(view_reg, ctx):
    model = htypes.model_commands_tests.sample_model_1()
    label_view = htypes.label.view("Sample label")
    navigator_piece = htypes.navigator.view(
        current_view=mosaic.put(label_view),
        current_model=mosaic.put(model),
        layout_k=None,
        prev=None,
        next=None,
        )
    navigator = view_reg.animate(navigator_piece, ctx)
    model_state = htypes.model_commands_tests.sample_model_state()
    piece = model_commands.open_model_commands(navigator, model_state)
    assert isinstance(piece, htypes.model_commands.model)


def _sample_fn_1(model, sample_service):
    return f'sample-fn-1: {sample_service}'


def _sample_fn_2(model, sample_service):
    return f'sample-fn-2: {sample_service}'


@mark.config_fixture('model_command_reg')
def model_command_reg_config(rpc_system_call_factory):
    system_fn_1 = ModelCommandFn(
        rpc_system_call_factory=rpc_system_call_factory,
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
    system_fn_2 = ModelCommandFn(
        rpc_system_call_factory=rpc_system_call_factory,
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


def test_list_model_commands(lcs, ctx, piece):
    item_list = model_commands.list_model_commands(piece, ctx, lcs)
    assert 'Sample command 2' in [item.name for item in item_list]


async def test_run_command(lcs, piece):
    navigator_rec = Mock()
    navigator_rec.view.open = AsyncMock()
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
        navigator=navigator_rec,
        )
    result = await model_commands.run_command(piece, current_item, ctx, lcs)
    navigator_rec.view.open.assert_awaited_once()
    assert navigator_rec.view.open.await_args.args[1] == 'sample-fn-2: a-service'


def test_format_model(piece):
    title = model_commands.format_model(piece)
    assert type(title) is str
