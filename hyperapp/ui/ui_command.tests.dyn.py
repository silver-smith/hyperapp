import weakref

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
        return 'a-piece'

    def widget_state(self, widget):
        return 'a-state'


def _sample_fn(view, state, sample_service):
    return 'sample-fn: {view.piece}, {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.config_fixture('view_ui_command_reg')
def view_ui_command_reg_config(data_to_res):
    properties = htypes.ui.command_properties(
        is_global=False,
        uses_state=False,
        remotable=False,
        )
    command_d_res = data_to_res(htypes.ui_command_tests.sample_command_d())
    impl = htypes.ui.ui_command_impl(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    command = htypes.ui.ui_command(
        d=mosaic.put(command_d_res),
        properties=properties,
        impl=mosaic.put(impl),
        )
    return [command]


async def test_view_commands(get_view_commands, ui_command_factory):
    view = PhonyView()
    widget = PhonyWidget()  # Should hold ref to it.
    ctx = Context(
        view=view,
        widget=weakref.ref(widget),
        )
    command_piece_list = get_view_commands(view)
    assert command_piece_list
    command = ui_command_factory(command_piece_list[0], ctx)
    result = await command.run()
    assert result == 'sample-fn: a-piece, a-state, a-service', repr(result)


def test_command_impl_from_piece():
    ctx = Context()
    piece = htypes.ui.ui_command_impl(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    impl = ui_command.ui_command_impl_from_piece(piece, ctx)
    assert impl
