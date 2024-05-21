import logging
from functools import cached_property

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    deduce_t,
    mark,
    mosaic,
    pyobj_creg,
    ui_command_creg,
    )
from .code.command import FnCommandBase

log = logging.getLogger(__name__)


class UiCommand(FnCommandBase):
    pass


@ui_command_creg.actor(htypes.ui.ui_command)
def ui_command_from_piece(piece, ctx):
    command_d = {pyobj_creg.invite(d) for d in piece.d}
    fn = pyobj_creg.invite(piece.function)
    return UiCommand(piece.name, command_d, ctx, fn, piece.params)


@mark.service
def ui_command_factory():
    def _ui_command_factory(view):
        piece_t = deduce_t(view.piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        universal_d_res = data_to_res(htypes.ui.universal_ui_command_d())
        command_list = [
            *association_reg.get_all((d_res, piece_t_res)),
            *association_reg.get_all(universal_d_res),
            ]
        return command_list
    return _ui_command_factory
