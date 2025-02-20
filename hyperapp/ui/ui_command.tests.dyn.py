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


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture
def view():
    return PhonyView()


# Should hold ref to it.
@mark.fixture
def widget():
    return PhonyWidget()


@mark.config_fixture('view_ui_command_reg')
def view_ui_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        raw_fn=_sample_fn,
        bound_fn=partial(_sample_fn, sample_service='a-service'),
        )
    command = ui_command.UnboundUiCommand(
        d=htypes.ui_command_tests.sample_command_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        groups=set(),
        )
    return {htypes.ui_command_tests.sample_view: [command]}


async def test_view_commands(get_view_commands, view, widget):
    lcs = Mock()
    lcs.get.return_value = None
    ctx = Context(
        view=view,
        widget=weakref.ref(widget),
        )
    command_list = get_view_commands(ctx, lcs, view)
    [unbound_command] = command_list
    bound_command = unbound_command.bind(ctx)
    result = await bound_command.run()
    assert result == 'sample-fn: a-state, a-service', repr(result)


def test_ui_command_from_piece():
    d = htypes.ui_command_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    piece = htypes.command.ui_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )
    command = ui_command.ui_command_from_piece(piece)
    assert isinstance(command, ui_command.UnboundUiCommand)


def test_ui_command_enumerator_from_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    piece = htypes.command.ui_command_enumerator(
        system_fn=mosaic.put(system_fn),
        )
    command = ui_command.ui_command_enumerator_from_piece(piece)
    assert isinstance(command, UnboundCommandEnumerator)


def test_ui_command_enumerator_reg(ui_command_enumerator_reg):
    view_t = htypes.ui_command_tests.sample_view
    commands = ui_command_enumerator_reg(view_t)
