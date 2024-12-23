import logging

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
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


def _view_item(item, shortcut):
    return htypes.command_list_view.item(
        ui_command_d=item.ui_command_d,
        model_command_d=item.model_command_d,
        name=item.name,
        groups=item.groups,
        repr=item.repr,
        shortcut=shortcut,
        text="",
        tooltip="",
        )


@mark.command
async def set_shortcut(piece, current_idx, current_item, lcs, feed_factory):
    feed = feed_factory(piece)
    command_d = pyobj_creg.invite(current_item.ui_command_d)
    shortcut = run_key_input_dialog()
    log.info("Set shortcut for %s: %r", command_d, shortcut)
    new_item = _view_item(current_item, shortcut=shortcut)
    key = {htypes.command.command_shortcut_lcs_d(), command_d}
    lcs.set(key, shortcut)
    await feed.send(ListDiff.Replace(current_idx, new_item))
