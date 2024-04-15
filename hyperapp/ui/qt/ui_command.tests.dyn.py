from . import htypes
from .services import (
    data_to_res,
    fn_to_res,
    mark,
    mosaic,
    )
from .tested.code import ui_command
from .tested.services import ui_command_factory


def _sample_fn(piece, state):
    return 123


class PhonyAssociationRegistry:

    def get_all(self, key):
        command_d_res = data_to_res(htypes.ui_command_tests.sample_command_d())
        fn_res = fn_to_res(_sample_fn)
        command = htypes.ui.ui_command(
            d=mosaic.put(command_d_res),
            name='sample_command',
            function=mosaic.put(fn_res),
            params=('piece', 'state'),
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
        return "Unused"

    def widget_state(self, widget):
        return None


async def test_ui_command_factory():
    model = None
    widget = PhonyWidget()  # Should hold ref to it.
    command_list = ui_command_factory(model, PhonyView(), widget, wrappers=[])
    assert command_list
    result = await command_list[0].run()
    assert result == 123, repr(result)
