import logging

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.command import d_res_ref_to_name
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


@mark.crud.get
def model_command_get(piece, ui_command_d):
    return htypes.rename_command.form(
        name=d_res_ref_to_name(ui_command_d),
        )


@mark.crud.update
def model_command_update(piece, ui_command_d, value, lcs, ctx, ui_model_command_items):
    model, model_t = web.summon_with_t(piece.model)
    model_state = web.summon(piece.model_state)
    prev_d = pyobj_creg.invite(ui_command_d)
    new_d_name = f'{value.name}_d'
    new_d_t = TRecord('custom_command', new_d_name)
    new_d = new_d_t()
    log.info("Rename command: %s -> %s", prev_d, new_d)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_item_list = ui_model_command_items(lcs, model_t, command_ctx)
    command_item_list.rename_command(prev_d, new_d)
