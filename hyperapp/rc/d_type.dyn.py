from hyperapp.boot.htypes import TRecord

from .services import (
    pyobj_creg,
    )


def d_type(types, type_module_name, name):
    d_name = name + '_d'
    try:
        piece = types[type_module_name][d_name]
    except KeyError:
        return TRecord(type_module_name, d_name)
    return pyobj_creg.animate(piece)


def k_type(types, type_module_name, name):
    k_name = name + '_k'
    try:
        piece = types[type_module_name][k_name]
    except KeyError:
        return TRecord(type_module_name, k_name)
    return pyobj_creg.animate(piece)
