import weakref
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
from .code.command_enumerator import UnboundCommandEnumerator
from .tested.code import ui_command


class PhonyWidget:
    pass


class PhonyView:

    @property
    def piece(self):
        return htypes.ui_command_tests.sample_view()

    def widget_state(self, widget):
        return 'a-state'


def _sample_command(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_command_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        raw_fn=_sample_command,
        bound_fn=partial(_sample_command, sample_service='a-service'),
        )


def _sample_command_enum(view, state, sample_service):
    return []


@mark.fixture
def sample_command_enum_fn():
    return htypes.command.ui_command_enum_fn(
        function=pyobj_creg.actor_to_ref(_sample_command_enum),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )


@mark.fixture
def sample_service():
    return 'a-service'


def test_command_enum_fn(ctx, sample_command_enum_fn):
    enum = ui_command.UiCommandEnumFn.from_piece(sample_command_enum_fn)
    assert enum.piece == sample_command_enum_fn
    result = enum.call(ctx, view="Sample view", state="Sample state")
    assert type(result) is tuple


@mark.fixture
def view():
    return PhonyView()


# Should hold ref to it.
@mark.fixture
def widget():
    return PhonyWidget()


@mark.config_fixture('view_ui_command_reg')
def view_ui_command_reg_config(sample_command_fn):
    command = ui_command.UnboundUiCommand(
        d=htypes.ui_command_tests.sample_command_d(),
        ctx_fn=sample_command_fn,
        properties=htypes.command.properties(False, False, False),
        groups=set(),
        )
    return {htypes.ui_command_tests.sample_view: [command]}


@mark.fixture
def ctx(view, widget):
    return Context(
        view=view,
        widget=weakref.ref(widget),
        )


async def test_view_commands(get_view_commands, view, ctx):
    command_list = get_view_commands(ctx, view)
    [unbound_command] = command_list
    bound_command = unbound_command.bind(ctx)
    result = await bound_command.run()
    assert result == 'sample-fn: a-state, a-service', repr(result)


async def test_view_element_commands(get_view_element_commands, view, ctx):
    command_list = get_view_element_commands(ctx, view)
    assert type(command_list) is list


def test_ui_command_from_piece(sample_command_fn):
    d = htypes.ui_command_tests.sample_command_d()
    piece = htypes.command.ui_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(sample_command_fn.piece),
        )
    command = ui_command.ui_command_from_piece(piece)
    assert isinstance(command, ui_command.UnboundUiCommand)
    assert command.piece == piece


def test_ui_command_enumerator_from_piece(sample_command_fn):
    piece = htypes.command.ui_command_enumerator(
        system_fn=mosaic.put(sample_command_fn.piece),
        )
    command = ui_command.ui_command_enumerator_from_piece(piece)
    assert isinstance(command, UnboundCommandEnumerator)


def test_ui_command_enumerator_reg(ui_command_enumerator_reg):
    view_t = htypes.ui_command_tests.sample_view
    commands = ui_command_enumerator_reg(view_t)
