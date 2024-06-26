from . import htypes
from .services import (
    model_command_impl_creg,
    )
from .code.command import CommandImpl


class IdentityModelCommandImpl(CommandImpl):

    def __init__(self, piece):
        super().__init__()
        self._piece = piece
        self._params = {'piece'}

    def __repr__(self):
        return 'identity'

    @property
    def name(self):
        return 'identity'

    @property
    def enabled(self):
        return True

    @property
    def disabled_reason(self):
        return None

    @property
    def params(self):
        return {
            'piece': self._piece,
            }

    async def _run(self):
        return self._piece


@model_command_impl_creg.actor(htypes.identity_command.identity_model_command_impl)
def identity_model_command_impl_from_piece(piece, ctx):
    return IdentityModelCommandImpl(piece)


def add_identity_command(piece):
    pass
