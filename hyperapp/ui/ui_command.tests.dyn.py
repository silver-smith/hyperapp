from .services import (
    association_reg,
    fn_to_res,
    pyobj_creg,
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


class PhonyWidget:
    pass


class PhonyCtl:

    def widget_state(self, widget):
        return None


def test_ui_command_factory():
    layout = "Nothing is here"
    command_list = ui_command_factory(layout, PhonyCtl())
    assert command_list
    command_list[0].bind(PhonyWidget()).run()
