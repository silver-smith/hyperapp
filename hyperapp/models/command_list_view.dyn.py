from . import htypes
from .code.mark import mark
from .code.directory import d_to_name


def command_item_to_view_item(data_to_ref, item):
    return htypes.command_list_view.item(
        ui_command_d=data_to_ref(item.d),
        model_command_d=data_to_ref(item.model_command_d),
        name=item.name,
        groups=", ".join(d_to_name(g) for g in item.command.groups) if item.enabled else "",
        repr=repr(item.command),
        shortcut="",
        text="",
        tooltip="",
        )


@mark.command
def set_shortcut(piece, current_item):
    pass
