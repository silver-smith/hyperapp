import logging

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.command import d_res_ref_to_name
from .code.model_commands import get_model_command_list

log = logging.getLogger(__name__)


@mark.crud.get
def model_command_get(piece, ui_command_d):
    return htypes.rename_command.form(
        name=d_res_ref_to_name(ui_command_d),
        )


@mark.crud.update
def model_command_update(piece, ui_command_d, value, ctx, lcs, data_to_ref, custom_ui_model_commands, get_ui_model_commands):
    model = web.summon(piece.model)
    model_t = deduce_t(model)
    prev_d = pyobj_creg.invite(ui_command_d)
    new_d_name = f'{value.name}_d'
    new_d_t = TRecord('custom_command', new_d_name)
    new_d = new_d_t()
    log.info("Rename command: %s -> %s", prev_d, new_d)
    command_list = get_model_command_list(piece, ctx, lcs, data_to_ref, get_ui_model_commands)
    d_to_command = {
        command.d: command
        for command in command_list
        }
    command = d_to_command[prev_d]
    new_command = htypes.command.custom_ui_model_command(
        ui_command_d=data_to_ref(new_d),
        model_command_d=data_to_ref(command.model_command_d),
        layout=command.layout,
        )
    custom_commands = custom_ui_model_commands(lcs, model_t)
    custom_commands.replace(prev_d, new_command)
