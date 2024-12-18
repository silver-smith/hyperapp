import logging

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.directory import d_to_name
from .code.key_input_dialog import run_key_input_dialog

log = logging.getLogger(__name__)


def command_item_to_view_item(data_to_ref, lcs, item):
    return htypes.command_list_view.item(
        ui_command_d=data_to_ref(item.d),
        model_command_d=data_to_ref(item.model_command_d),
        name=item.name,
        groups=", ".join(d_to_name(g) for g in item.command.groups) if item.enabled else "",
        repr=repr(item.command),
        shortcut=lcs.get({htypes.command.command_shortcut_lcs_d(), item.d}) or "",
        text="",
        tooltip="",
        )


@mark.command
def set_shortcut(piece, current_item, lcs):
    command_d = pyobj_creg.invite(current_item.ui_command_d)
    shortcut = run_key_input_dialog()
    log.info("Set shortcut for %s: %r", command_d, shortcut)
    key = {htypes.command.command_shortcut_lcs_d(), command_d}
    lcs.set(key, shortcut)
