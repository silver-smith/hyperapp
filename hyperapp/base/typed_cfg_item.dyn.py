from .services import (
    pyobj_creg,
    web,
    )


def resolve_typed_cfg_item(piece):
    t = pyobj_creg.invite(piece.t)
    return (t, piece)


def resolve_typed_cfg_value(piece, key, system, service_name):
    return web.summon(piece.value)


def resolve_typed_fn_cfg_value(piece, key, system, service_name):
    system_fn_creg = system.resolve_service('system_fn_creg')
    return system_fn_creg.invite(piece.system_fn)
