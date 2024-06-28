from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    data_to_ref,
    model_command_impl_creg,
    mosaic,
    get_ui_model_commands,
    set_ui_model_commands,
    web,
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
    return IdentityModelCommandImpl(ctx.piece)


def add_identity_command(piece, lcs):
    model = web.summon(piece.model)
    command_list = get_ui_model_commands(lcs, model)
    model_impl = htypes.identity_command.identity_model_command_impl()
    ui_impl = htypes.ui.ui_model_command_impl(
        model_command_impl=mosaic.put(model_impl),
        layout=None,
        )
    d_t = TRecord('identity_command', 'identity_d')
    command = htypes.ui.command(
        d=data_to_ref(d_t()),
        impl=mosaic.put(ui_impl),
        )
    command_list.append(command)
    set_ui_model_commands(lcs, model, command_list)
