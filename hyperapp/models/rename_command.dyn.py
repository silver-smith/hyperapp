import logging

from . import htypes
from .code.mark import mark
from .code.command import d_res_ref_to_name

log = logging.getLogger(__name__)


@mark.crud.get
def model_command_get(piece, ui_command_d):
    return htypes.rename_command.form(
        name=d_res_ref_to_name(ui_command_d),
        )


@mark.crud.update
def model_command_update(piece, ui_command_d, value):
    old_name = d_res_ref_to_name(ui_command_d)
    log.info("Rename command: %s -> %s", old_name, value.name)
    new_d_name = f'{value.name}_d'
