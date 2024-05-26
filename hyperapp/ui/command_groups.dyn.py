from . import htypes
from .code.command import CommandKind


def default_command_groups(properties, kind):
    global_d = htypes.command_groups.global_d()
    view_d = htypes.command_groups.view_d()
    model_d = htypes.command_groups.model_d()
    pane_1_d = htypes.command_groups.pane_1_d()
    pane_2_d = htypes.command_groups.pane_2_d()
    remotable_d = htypes.command_groups.remotable_d()

    groups = set()
    if properties.is_global:
        if properties.uses_state:
            groups.add(pane_2_d)
        else:
            groups.add(global_d)
    elif kind == CommandKind.VIEW:
        groups.add(view_d)
    elif kind == CommandKind.MODEL:
        if properties.uses_state:
            groups.add(pane_2_d)
        else:
            groups.add(model_d)
            groups.add(pane_1_d)
    if properties.remotable:
        groups.add(remotable_d)

    return groups
