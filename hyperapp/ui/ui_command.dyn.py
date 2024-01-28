import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


@mark.service
def ui_command_factory():
    def _ui_command_factory(view_piece):
        piece_t = deduce_value_type(view_piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        fn_res_list = association_reg.get_all((d_res, piece_t_res))
        return fn_res_list
    return _ui_command_factory
