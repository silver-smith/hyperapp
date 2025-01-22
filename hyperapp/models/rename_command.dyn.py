import logging

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark
from .code.directory import d_res_ref_to_name, name_to_d
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


@mark.crud.rename_to(commit_action='rename')
def model_command_rename_to(piece, ui_command_d):
    return htypes.rename_command.form(
        name=d_res_ref_to_name(ui_command_d),
        )


@mark.crud.rename
def model_command_rename(piece, ui_command_d, value, lcs, ctx, ui_model_command_items):
    model, model_t = web.summon_with_t(piece.model)
    model_state = web.summon(piece.model_state)
    prev_d = web.summon(ui_command_d)
    new_d = name_to_d('custom_command', value.name)
    log.info("Rename command: %s -> %s", prev_d, new_d)
    command_ctx = model_command_ctx(ctx, model, model_state)
    command_item_list = ui_model_command_items(lcs, model_t, command_ctx)
    command_item_list.rename_command(prev_d, new_d)
