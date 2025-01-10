from hyperapp.boot.htypes import TRecord

from .services import (
    pyobj_creg,
    )


def d_type(types, type_module_name, name):
    d_name = name + '_d'
    t_piece = types.get(type_module_name, d_name)
    if t_piece is not None:
        return pyobj_creg.animate(t_piece)
    return TRecord(type_module_name, d_name)
