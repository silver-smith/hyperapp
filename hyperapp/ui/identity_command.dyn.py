from functools import cached_property

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.command import CommandKind, BoundCommandBase, UnboundCommandBase
from .code.ui_model_command import UnboundUiModelCommand
from .code.model_commands import ui_command_to_item


class UnboundIdentityModelCommand(UnboundCommandBase):

    @classmethod
    @mark.actor.command_creg
    def from_piece(cls, piece):
        d = pyobj_creg.invite(piece.d)
        return cls(d)

    def __repr__(self):
        return f"<UnboundIdentityModelCommand>"

    @property
    def properties(self):
        return htypes.command.properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def bind(self, ctx):
        return BoundIdentityModelCommand(self._d, ctx)


class BoundIdentityModelCommand(BoundCommandBase):

    def __init__(self, d, ctx):
        super().__init__(d)
        self._ctx = ctx

    @property
    def enabled(self):
        return not self._missing_params

    @property
    def disabled_reason(self):
        params = ", ".join(self._missing_params)
        return f"Params not ready: {params}"

    async def run(self):
        return self._ctx.model

    @cached_property
    def _missing_params(self):
        return {'model'} - self._ctx.as_dict().keys()


@mark.command
async def add_identity_command(piece, lcs, data_to_ref, feed_factory, model_view_creg, visualizer, command_creg, custom_ui_model_commands):
    feed = feed_factory(piece)
    model = web.summon(piece.model)
    model_t = deduce_t(model)
    new_d_name = 'identity_d'
    new_d_t = TRecord('custom_command', new_d_name)
    command_d = new_d_t()
    model_command_piece = htypes.identity_command.identity_command(
        d=data_to_ref(command_d),
        )
    rec = htypes.command.custom_ui_command(
        ui_command_d=data_to_ref(command_d),
        model_command=mosaic.put(model_command_piece),
        layout=None,
        )
    custom_commands = custom_ui_model_commands(lcs, model_t)
    custom_commands.set(rec)
    model_command = command_creg.animate(model_command_piece)
    ui_command = UnboundUiModelCommand(model_view_creg, visualizer, lcs, command_d, model_command)
    new_item = ui_command_to_item(data_to_ref, ui_command)
    await feed.send(ListDiff.Append(new_item))
