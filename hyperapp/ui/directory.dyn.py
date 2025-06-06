from hyperapp.boot.htypes import TRecord

from .services import (
    web,
    )


def d_to_name(d):
    name = d._t.name
    assert name.endswith('_d'), repr(name)
    return name[:-2]


def k_to_name(k):
    name = k._t.name
    assert name.endswith('_k'), repr(name)
    return name[:-2]


def d_res_ref_to_name(d_ref):
    d = web.summon(d_ref)
    return d_to_name(d)


def name_to_d(module_name, name):
    d_name = f'{name}_d'
    d_t = TRecord(module_name, d_name)
    return d_t()
