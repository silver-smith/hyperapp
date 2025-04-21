from unittest.mock import Mock, AsyncMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import ModelCommandFn, ModelCommandAddFn, UnboundModelCommand
from .fixtures import error_view_fixtures
from .tested.code import ui_model_command


def _sample_fn_1(model, state):
    return f'sample-fn-1: {state}'


def _sample_fn_2(model, state):
    return '5'


def _sample_fn_3(model, state):
    return f'sample-fn-3: {state}'


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(rpc_system_call_factory):
    system_fn = ModelCommandFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('model', 'state'),
        service_params=(),
        raw_fn=_sample_fn_1,
        bound_fn=_sample_fn_1,
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_model_command_1_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.config_fixture('model_command_reg')
def model_command_reg_config(rpc_system_call_factory, model_servant):
    system_fn = ModelCommandAddFn(
        rpc_system_call_factory=rpc_system_call_factory,
        model_servant=model_servant,
        ctx_params=('model', 'state'),
        service_params=(),
        raw_fn=_sample_fn_2,
        bound_fn=_sample_fn_2,
        )
    command = UnboundModelCommand(
        d=htypes.ui_model_command_tests.sample_model_command_2_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    model_t = htypes.ui_model_command_tests.sample_model
    return {model_t: [command]}


@mark.fixture
def lcs():
    command_3 = htypes.command.custom_ui_model_command(
        ui_command_d=mosaic.put(htypes.ui_model_command_tests.sample_command_3_d()),
        model_command_d=mosaic.put(htypes.ui_model_command_tests.sample_model_command_2_d()),
        )
    fn_3 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn_3),
        ctx_params=('model', 'state'),
        service_params=(),
        )
    model_command_3 = htypes.command.model_command(
        d=mosaic.put(htypes.ui_model_command_tests.sample_model_command_3_d()),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(fn_3),
        )
    command_4 = htypes.command.custom_ui_command(
        ui_command_d=mosaic.put(htypes.ui_model_command_tests.sample_command_4_d()),
        model_command=mosaic.put(model_command_3),
        )
    command_list = htypes.command.custom_model_command_list(
        commands=(
            mosaic.put(command_3),
            mosaic.put(command_4),
            )
        )
    lcs = Mock()
    lcs.get.return_value = command_list
    return lcs


def test_set_custom_ui_model_command(custom_ui_model_commands, lcs):
    model_t = htypes.ui_model_command_tests.sample_model
    command = htypes.command.custom_ui_model_command(
        ui_command_d=mosaic.put(htypes.ui_model_command_tests.sample_command_2_d()),
        model_command_d=mosaic.put(htypes.ui_model_command_tests.sample_model_command_2_d()),
        )
    custom_commands = custom_ui_model_commands(lcs, model_t)
    custom_commands.set(command)
    lcs.get.assert_called_once()
    lcs.set.assert_called_once()


def test_get_ui_model_commands(get_ui_model_commands, lcs):
    ctx = Context()
    model_t = htypes.ui_model_command_tests.sample_model
    command_list = get_ui_model_commands(lcs, model_t, ctx)
    command_d_set = {
        command.d for command in command_list
        }
    assert command_d_set == {
        htypes.ui_model_command_tests.sample_model_command_1_d(),
        htypes.ui_model_command_tests.sample_model_command_2_d(),
        htypes.ui_model_command_tests.sample_command_3_d(),
        htypes.ui_model_command_tests.sample_command_4_d(),
        }, command_d_set
    for cmd in command_list:
        assert isinstance(cmd, ui_model_command.UnboundUiModelCommand)


def test_ui_global_command_items_get_items(ui_global_command_items, lcs):
    command_items = ui_global_command_items(lcs)
    d_set = {
        item.d for item in command_items.items()
        }
    assert d_set == {
        htypes.ui_model_command_tests.sample_model_command_1_d(),  # from global commands.
        # sample_command_3_d from lcs has no matching global command.
        htypes.ui_model_command_tests.sample_command_4_d(),  # configured by lcs.
        }, d_set


def test_split_command_result():
    result = htypes.command.command_result(
        model=mosaic.put('sample-model'),
        key=None,
        diff=None,
        )
    model, key = ui_model_command.split_command_result(result)
    assert model == 'sample-model'


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config():
    def k(t):
        return htypes.ui.model_layout_k(pyobj_creg.actor_to_ref(t))
    return {
        k(htypes.builtin.string): htypes.text.edit_view(
            adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
            ),
        }


async def test_command_run_open_view(get_ui_model_commands, lcs):
    model_t = htypes.ui_model_command_tests.sample_model
    model = model_t()
    navigator_rec = Mock()
    ctx = Context(
        navigator=navigator_rec,
        ).push(
        model=model,
        piece=model,
        state="Sample state",
        )
    command_list = get_ui_model_commands(lcs, model_t, ctx)
    d_to_command = {
        command.d: command for command in command_list
        }
    command_d = htypes.ui_model_command_tests.sample_model_command_1_d()
    unbound_command = d_to_command[command_d]
    bound_command = unbound_command.bind(ctx)
    await bound_command.run()
    navigator_rec.view.open.assert_called_once()


def _sample_model_servant(piece):
    return [
        htypes.ui_model_command_tests.sample_item(
            id=str(idx),
            value=idx * 100,
            )
        for idx in range(10)
        ]


@mark.fixture
def sample_servant_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece',),
        service_params=(),
        raw_fn=_sample_model_servant,
        bound_fn=_sample_model_servant,
        )


@mark.fixture
def sample_feed():
    return AsyncMock()


@mark.fixture
def feed_factory(sample_feed, model):
    assert isinstance(model, htypes.ui_model_command_tests.sample_model)
    return sample_feed


async def test_command_run_process_diff(model_servant, get_ui_model_commands, lcs, sample_servant_fn, sample_feed):
    model_t = htypes.ui_model_command_tests.sample_model
    model = model_t()
    model_servant(model).set_servant_fn(
        key_field='id',
        key_field_t=htypes.builtin.string,
        fn=sample_servant_fn,
        )
    navigator_rec = Mock()
    ctx = Context(
        navigator=navigator_rec,
        ).push(
        model=model,
        piece=model,
        state="Sample state",
        )
    command_list = get_ui_model_commands(lcs, model_t, ctx)
    d_to_command = {
        command.d: command for command in command_list
        }
    command_d = htypes.ui_model_command_tests.sample_model_command_2_d()
    unbound_command = d_to_command[command_d]
    bound_command = unbound_command.bind(ctx)
    await bound_command.run()
    sample_feed.send.assert_awaited()
    navigator_rec.view.set_current_key.assert_called_once()
    navigator_rec.view.open.assert_not_called()
