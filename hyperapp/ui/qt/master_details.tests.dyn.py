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
from .fixtures import qapp_fixtures
from .tested.code import master_details


def _sample_fn(model, sample_service):
    return f'sample-fn: {sample_service}'


@mark.fixture
def command_d():
    return htypes.master_details_tests.sample_command_d()


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(partial_ref, command_d):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('model',),
        service_params=('sample_service',),
        raw_fn=_sample_fn,
        bound_fn=partial(_sample_fn, sample_service='a-service'),
        )
    command = UnboundModelCommand(
        d=command_d,
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.fixture
def master_piece():
    master_adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.readonly_view(mosaic.put(master_adapter))


@mark.fixture
def piece(master_piece, command_d):
    return htypes.master_details.view(
        master_view=mosaic.put(master_piece),
        details_command_d=mosaic.put(command_d),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )


@mark.fixture
def state():
    master_state = htypes.text.state('')
    return htypes.master_details.state(
        master_state=mosaic.put(master_state),
        details_state=mosaic.put(htypes.label.state()),
        )


@mark.fixture
def ctx():
    return Context(
        lcs=Mock(),
        )


@mark.fixture.obj
def model():
    return "Sample string"


@mark.fixture
def model_state():
    return htypes.master_details_tests.sample_model_state()


def test_view(qapp, piece, state, model, ctx):
    view = master_details.MasterDetailsView.from_piece(piece, model, ctx)
    assert isinstance(view.piece, htypes.master_details.view)
    widget = view.construct_widget(state, ctx)
    assert widget
    state = view.widget_state(widget)
    assert isinstance(state, htypes.master_details.state)


async def test_run_details_command(qapp, piece, state, model, ctx):
    view = master_details.MasterDetailsView.from_piece(piece, model, ctx)
    rctx = Context(
        model_state=model_state,
        )
    widget = Mock()
    ctl_hook = Mock()
    view.set_controller_hook(ctl_hook)
    await view.children_context_changed(ctx, rctx, widget)
    ctl_hook.element_replaced.assert_called_once()


def test_wrap_master_details(qapp, master_piece, model, model_state, ctx):
    hook = Mock()
    view = Mock()
    piece = master_details.master_details(model, model_state, master_piece, ctx)
    assert isinstance(piece, htypes.master_details.view)


def test_unwrap_master_details(qapp, piece, state, model, ctx):
    view = master_details.MasterDetailsView.from_piece(piece, model, ctx)
    hook = Mock()
    master_details.unwrap_master_details(model, view, state, hook, ctx)
    hook.replace_view.assert_called_once()
