# List commands for current model.

import logging

from . import htypes
from .services import (
    model_command_creg,
    model_command_factory,
    mosaic,
    web,
    )

log = logging.getLogger(__name__)


def list_model_commands(piece, ctx):
    model = web.summon(piece.model)
    command_list = model_command_factory(model)
    return [
        htypes.model_commands.item(
            command=mosaic.put(command),
            name=command.name,
            d=str(command.d),
            params=", ".join(command.params),
            )
        for command in command_list
        ]


async def run_command(piece, current_item, ctx):
    model = web.summon(piece.model)
    command_ctx = ctx.clone_with(
        piece=model,
        )
    command = model_command_creg.invite(current_item.command, command_ctx)
    piece = await command.run()
    log.info("Run command: command result: %s", piece)
    return piece


def open_model_commands(piece):
    return htypes.model_commands.model_commands(
        model=mosaic.put(piece),
        )
