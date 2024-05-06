# List commands for current model.

from . import htypes
from .services import (
    model_command_factory,
    mosaic,
    web,
    )


def list_model_commands(piece, ctx):
    model = web.summon(piece.model)
    command_list = model_command_factory(model)
    return [
        htypes.model_commands.item(
            name=command.name,
            d=str(command.d),
            params=", ".join(command.params),
            )
        for command in command_list
        ]


def open_model_commands(piece):
    return htypes.model_commands.model_commands(
        model=mosaic.put(piece),
        )
