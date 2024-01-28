from .services import (
    fn_to_res,
    mark,
    )
from .tested.code import ui_command
from .tested.services import ui_command_factory


def _sample_fn(layout, state):
    pass


class PhonyAssociationRegistry:

    def get_all(self, key):
        return [fn_to_res(_sample_fn)]


@mark.service
def association_reg():
    return PhonyAssociationRegistry()


def test_ui_command_factory():
    view_piece = "Nothing is here"
    fn_res_list = ui_command_factory(view_piece)
    assert fn_res_list
