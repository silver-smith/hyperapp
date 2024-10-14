# List global commands.

import logging

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import d_to_name
from .code.ui_model_command import wrap_model_command_to_ui_command

log = logging.getLogger(__name__)


@mark.model
def list_global_commands(piece, lcs, data_to_ref, global_model_command_reg, model_view_creg, visualizer):
    command_list = [
        wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, cmd)
        for cmd in global_model_command_reg
        ]
    return [
        htypes.global_commands.item(
            ui_command_d=data_to_ref(command.d),
            model_command_d=data_to_ref(command.model_command_d),
            name=command.name,
            groups=", ".join(d_to_name(g) for g in command.groups),
            repr=repr(command),
            )
        for command in command_list
        if not command.properties.uses_state
        ]


@mark.command
async def run_command(piece, current_item, lcs, ctx, global_model_command_reg, model_view_creg, visualizer):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    command_list = [
        wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, cmd)
        for cmd in global_model_command_reg
        ]
    command_d = pyobj_creg.invite(current_item.ui_command_d)
    unbound_command = next(cmd for cmd in command_list if cmd.d == command_d)
    bound_command = unbound_command.bind(ctx)
    piece = await bound_command.run()
    log.info("Run command: command result: %s", piece)
    return piece


@mark.global_command
def open_global_commands():
    return htypes.global_commands.view()
