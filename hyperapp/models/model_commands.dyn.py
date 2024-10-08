# List commands for current model.

import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.model
async def list_model_commands(piece, ctx, lcs, get_ui_model_commands):
    model = web.summon(piece.model)
    command_list = await get_ui_model_commands(lcs, model, ctx)
    return [
        htypes.model_commands.item(
            # command=mosaic.put(command),
            name=command.name,
            repr=repr(command),
            )
        for command in command_list
        ]


async def run_command(piece, current_item, ctx):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    model = web.summon(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = ctx.push(
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )
    command_piece = web.summon(current_item.command)
    command = ui_command_factory(command_piece, command_ctx)
    piece = await command.run()
    log.info("Run command: command result: %s", piece)
    return piece


@mark.global_command
def open_model_commands(piece, model_state):
    return htypes.model_commands.model_commands(
        model=mosaic.put(piece),
        model_state=mosaic.put(model_state),
        )
