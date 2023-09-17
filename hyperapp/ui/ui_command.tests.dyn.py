from .tested.services import (
    ui_command_factory,
    )


class PhonyWidget:
    state = None


def test_ui_command_factory():
    layout = "Nothing is here"
    command_list = ui_command_factory(layout)
    assert command_list
    command_list[0].bind(PhonyWidget()).run()
