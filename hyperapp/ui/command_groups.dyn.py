from . import htypes
from .code.command import CommandKind


def default_command_groups(properties, kind):
    global_d = htypes.command_groups.global_d()
    view_d = htypes.command_groups.view_d()
    model_d = htypes.command_groups.model_d()
    context_d = htypes.command_groups.context_d()
    remotable_d = htypes.command_groups.remotable_d()

    groups = set()
    if properties.is_global:
        groups.add(global_d)
    if kind == CommandKind.MODEL:
        groups.add(model_d)
        if properties.uses_state:
            groups.add(context_d)
    if properties.remotable:
        groups.add(remotable_d)

    return groups
