import weakref
from functools import partial

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import ui_command


class PhonyWidget:
    pass


class PhonyView:

    @property
    def piece(self):
        return htypes.ui_command_tests.view()

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
def view_ui_command_reg_config(view, widget):
    ctx = Context(
        view=view,
        widget=weakref.ref(widget),
        )
    command = ui_command.UiCommand(
        d=htypes.ui_command_tests.sample_command_d(),
        fn=partial(_sample_fn, sample_service='a-service'),
        ctx_params=('view', 'state'),
        ctx=ctx,
        system_kw={},
        groups=set(),
        )
    return {htypes.ui_command_tests.view: [command]}


async def test_view_commands(view, get_view_commands):
    command_list = get_view_commands(view)
    [command] = command_list
    result = await command.run()
    assert result == 'sample-fn: a-state, a-service', repr(result)
