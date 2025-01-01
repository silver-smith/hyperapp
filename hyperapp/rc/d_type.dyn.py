from hyperapp.common.htypes import TRecord

from .services import (
    pyobj_creg,
    )


def d_type(types, module_name, name):
    d_name = name + '_d'
    type_module = module_name.split('.')[-1]
    t_piece = types.get(type_module, d_name)
    if t_piece is not None:
        return pyobj_creg.animate(t_piece)
    return TRecord(type_module, d_name)
