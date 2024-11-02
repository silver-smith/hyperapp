# List commands for current model.

import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.command import d_to_name
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


@mark.model
def list_model_commands(piece, ctx, lcs, data_to_ref, get_ui_model_commands):
    model = web.summon(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_list = get_ui_model_commands(lcs, model, command_ctx)
    return [
        htypes.model_commands.item(
            ui_command_d=data_to_ref(command.d),
            model_command_d=data_to_ref(command.model_command_d),
            name=command.name,
            groups=", ".join(d_to_name(g) for g in command.groups),
            repr=repr(command),
            )
        for command in command_list
        if not command.properties.is_global or command.properties.uses_state
        ]


@mark.command
async def run_command(piece, current_item, ctx, lcs, get_ui_model_commands):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    model = web.summon(piece.model)
    model_state = web.summon(piece.model_state)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_list = get_ui_model_commands(lcs, model, command_ctx)
    command_d = pyobj_creg.invite(current_item.ui_command_d)
    unbound_command = next(cmd for cmd in command_list if cmd.d == command_d)
    bound_command = unbound_command.bind(command_ctx)
    piece = await bound_command.run()
    log.info("Run command: command result: %s", piece)
    return piece


@mark.global_command
def open_model_commands(piece, model_state):
    return htypes.model_commands.view(
        model=mosaic.put(piece),
        model_state=mosaic.put(model_state),
        )
