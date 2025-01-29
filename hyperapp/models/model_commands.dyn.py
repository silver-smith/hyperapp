# List commands for current model.

import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.model_command import model_command_ctx
from .code.command_list_model import command_item_to_model_item

log = logging.getLogger(__name__)


@mark.model
def list_model_commands(piece, ctx, lcs, ui_model_command_items, shortcut_reg):
    model, model_t = web.summon_with_t(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_item_list = ui_model_command_items(lcs, model_t, command_ctx)
    return [
        command_item_to_model_item(shortcut_reg, lcs, item)
        for item in command_item_list.items()
        if not item.is_pure_global
        ]


@mark.command
async def run_command(piece, current_item, ctx, lcs, ui_model_command_items):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    model, model_t = web.summon_with_t(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_item_list = ui_model_command_items(lcs, model_t, command_ctx)
    command_d = web.summon(current_item.ui_command_d)
    command_item = command_item_list[command_d]
    if not command_item.enabled:
        log.warning("Command %s is disabled; not running", command_item.name)
        return None
    unbound_command = command_item.command
    bound_command = unbound_command.bind(command_ctx)
    piece = await bound_command.run()
    log.info("Run command: command result: %s", piece)
    return piece


@mark.global_command
def open_model_commands(piece, model_state):
    return htypes.model_commands.model(
        model=mosaic.put(piece),
        model_state=mosaic.put(model_state),
        )
