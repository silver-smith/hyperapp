# List commands for current model.

import logging

from . import htypes
from .services import (
    model_command_factory,
    model_commands,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.command import d_res_ref_to_name

log = logging.getLogger(__name__)


def list_model_commands(piece, ctx):
    model = web.summon(piece.model)
    command_list = model_commands(model)
    return [
        htypes.model_commands.item(
            command=mosaic.put(command),
            name=d_res_ref_to_name(command.d),
            impl=str(web.summon(command.impl)),
            )
        for command in command_list
        ]


async def run_command(piece, current_item, ctx):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    model = web.summon(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = ctx.clone_with(
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )
    command_piece = web.summon(current_item.command)
    command = model_command_factory(command_piece, command_ctx)
    piece = await command.run()
    log.info("Run command: command result: %s", piece)
    return piece


def open_model_commands(piece, model_state):
    return htypes.model_commands.model_commands(
        model=mosaic.put(piece),
        model_state=mosaic.put(model_state),
        )
