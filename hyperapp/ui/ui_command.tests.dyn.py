from .services import (
    fn_to_res,
    mark,
    )
from .tested.code import ui_command
from .tested.services import ui_command_factory


def _sample_fn(layout, state):
    return 123


class PhonyAssociationRegistry:

    def get_all(self, key):
        return [fn_to_res(_sample_fn)]


@mark.service
def association_reg():
    return PhonyAssociationRegistry()


class PhonyWidget:
    pass


class PhonyView:

    def widget_state(self, piece, widget):
        return None


async def test_ui_command_factory():
    view_piece = "Nothing is here"
    widget = PhonyWidget()  # Should hold ref to it.
    command_list = ui_command_factory(view_piece, PhonyView(), widget, wrappers=[])
    assert command_list
    result = await command_list[0].run()
    assert result == 123, repr(result)
