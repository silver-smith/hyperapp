# List global commands.

import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command_list_model import command_item_to_model_item

log = logging.getLogger(__name__)


@mark.model
def list_global_commands(piece, lcs, ui_global_command_items, shortcut_reg):
    command_item_list = ui_global_command_items(lcs)
    return [
        command_item_to_model_item(shortcut_reg, lcs, item)
        for item in command_item_list.items()
        if item.is_global
        ]


@mark.command
async def run_command(piece, current_item, lcs, ctx, ui_global_command_items):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    command_d = web.summon(current_item.ui_command_d)
    command_item_list = ui_global_command_items(lcs)
    command_item = command_item_list[command_d]
    if not command_item.enabled:
        log.warning("Command %s is disabled; not running", command_item.name)
        return None
    unbound_command = command_item.command
    bound_command = unbound_command.bind(ctx)
    piece = await bound_command.run()
    log.info("Run command: command result: %s", piece)
    return piece


@mark.selector.get
def global_command_get(value):
    return htypes.global_commands.model()


@mark.selector.pick
def global_command_pick(piece, current_item):
    return htypes.global_commands.command_arg(
        d=current_item.model_command_d,
        )


@mark.global_command
def open_global_commands():
    return htypes.global_commands.model()
