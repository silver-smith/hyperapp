# List commands for current model.

from . import htypes
from .services import (
    mosaic,
    )


def open_model_commands(piece):
    return htypes.model_commands.model_commands(
        model=mosaic.put(piece),
        )
