from . import htypes
from .code.command import CommandKind
from .tested.code import command_groups


def test_default_command_groups():
    properties = htypes.ui.command_properties(
        is_global=False,
        uses_state=False,
        remotable=False,
        )
    kind = CommandKind.MODEL
    groups = command_groups.default_command_groups(properties, kind)
    assert type(groups) is set
