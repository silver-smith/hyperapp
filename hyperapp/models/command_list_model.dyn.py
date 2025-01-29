import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.directory import d_to_name
from .code.key_input_dialog import run_key_input_dialog

log = logging.getLogger(__name__)


def _get_command_text(lcs, d):
    return ""


def _get_command_tooltip(lcs, d):
    return ""


def command_item_to_model_item(shortcut_reg, lcs, item):
    return htypes.command_list_model.item(
        ui_command_d=mosaic.put(item.d),
        model_command_d=mosaic.put(item.model_command_d),
        name=item.name,
        groups=", ".join(d_to_name(g) for g in item.command.groups) if item.enabled else "",
        repr=repr(item.command),
        shortcut=shortcut_reg.get(item.d) or "",
        text=_get_command_text(lcs, item.d),
        tooltip=_get_command_tooltip(lcs, item.d),
        )


def _view_item(item, shortcut):
    return htypes.command_list_model.item(
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
async def set_shortcut(piece, current_idx, current_item, shortcut_reg, feed_factory):
    feed = feed_factory(piece)
    command_d = web.summon(current_item.ui_command_d)
    shortcut = run_key_input_dialog()
    if not shortcut:
        return
    log.info("Set shortcut for %s: %r", command_d, shortcut)
    new_item = _view_item(current_item, shortcut=shortcut)
    shortcut_reg[command_d] = shortcut
    await feed.send(ListDiff.Replace(current_idx, new_item))


@mark.crud.get
def command_get(piece, ui_command_d, lcs):
    return htypes.command_list_model.form(
        text="",
        tooltip="",
        )


@mark.crud.update
def command_update(piece, ui_command_d, value, lcs):
    d = web.summon(ui_command_d)
    prev_text = _get_command_text(lcs, d)
    prev_tooltip = _get_command_tooltip(lcs, d)
    if value.text != prev_text:
        log.info("Set text for %s: %r", d, value.text)
    if value.tooltip != prev_tooltip:
        log.info("Set tooltip for %s: %r", d, value.tooltip)
