from .tested.services import (
    ui_command_factory,
    )


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
