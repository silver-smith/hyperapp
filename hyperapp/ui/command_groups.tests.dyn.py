from . import htypes
from .tested.code import command_groups


def test_default_command_groups():
    properties = htypes.ui.command_properties(
        is_global=False,
        uses_state=False,
        remotable=False,
        )
    groups = command_groups.default_command_groups(properties)
    assert type(groups) is set
