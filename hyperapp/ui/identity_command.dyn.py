from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    data_to_ref,
    model_command_impl_creg,
    mosaic,
    get_ui_model_commands,
    set_ui_model_commands,
    )
from .code.command import CommandImpl


class IdentityModelCommandImpl(CommandImpl):

    def __init__(self, piece):
        super().__init__()
        self._piece = piece

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
        return {'piece': self._piece}

    async def _run(self):
        return self._piece


@model_command_impl_creg.actor(htypes.identity_command.identity_model_command_impl)
def identity_model_command_impl_from_piece(piece, ctx):
    return IdentityModelCommandImpl(piece)


def add_identity_command(piece, lcs):
    command_list = get_ui_model_commands(lcs, piece)
    impl = htypes.identity_command.identity_model_command_impl()
    d_t = TRecord('identity_command', 'identity')
    command = htypes.ui.command(
        d=data_to_ref(d_t()),
        impl=mosaic.put(impl),
        )
    command_list.append(command)
    set_ui_model_commands(lcs, piece, command_list)
