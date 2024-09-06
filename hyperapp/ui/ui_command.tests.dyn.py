import weakref

from . import htypes
from .services import (
    data_to_res,
    fn_to_ref,
    mark,
    mosaic,
    )
from .code.context import Context
from .tested.code import ui_command
from .tested.services import ui_command_factory, list_view_commands


def _sample_fn(view, state):
    return view.piece + state


class PhonyAssociationRegistry:

    def __getitem__(self, key):
        return htypes.ui.command_properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def get_all(self, key):
        command_d_res = data_to_res(htypes.ui_command_tests.sample_command_d())
        impl = htypes.ui.ui_command_impl(
            function=fn_to_ref(_sample_fn),
            params=('view', 'state'),
            )
        command = htypes.ui.ui_command(
            d=mosaic.put(command_d_res),
            impl=mosaic.put(impl),
            )
        return [command]


@mark.service
def association_reg():
    return PhonyAssociationRegistry()


class PhonyWidget:
    pass


class PhonyView:

    @property
    def piece(self):
        return 23

    def widget_state(self, widget):
        return 100


async def test_list_view_commands():
    view = PhonyView()
    widget = PhonyWidget()  # Should hold ref to it.
    ctx = Context(
        view=view,
        widget=weakref.ref(widget),
        )
    command_piece_list = list_view_commands(view)
    assert command_piece_list
    command = ui_command_factory(command_piece_list[0], ctx)
    result = await command.run()
    assert result == 123, repr(result)


def test_command_impl_from_piece():
    ctx = Context()
    piece = htypes.ui.ui_command_impl(
        function=fn_to_ref(_sample_fn),
        params=('view', 'state'),
        )
    impl = ui_command.ui_command_impl_from_piece(piece, ctx)
    assert impl
    assert impl.properties
