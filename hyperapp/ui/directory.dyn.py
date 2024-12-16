from hyperapp.common.htypes import TRecord

from .services import (
    pyobj_creg,
    )


def d_to_name(d):
    name = d._t.name
    assert name.endswith('_d'), repr(name)
    return name[:-2]


def d_res_ref_to_name(d_ref):
    d = pyobj_creg.invite(d_ref)
    return d_to_name(d)


def name_to_d(module_name, name):
    d_name = f'{name}_d'
    d_t = TRecord(module_name, d_name)
    return d_t()
