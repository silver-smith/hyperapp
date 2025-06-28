from . import htypes
from .services import (
    pyobj_creg,
    web,
    )


def resolve_typed_cfg_item(piece):
    t = pyobj_creg.invite(piece.t)
    value = web.summon(piece.value)
    return (t, value)


def resolve_typed_cfg_value(piece, key, system, service_name):
    assert 0, (key, piece, service_name)  # TODO: Remove.
    return web.summon(piece.value)


def resolve_typed_fn_cfg_value(piece, key, system, service_name):
    system_fn_creg = system.resolve_service('system_fn_creg')
    return system_fn_creg.invite(piece.system_fn)


def typed_cfg_item_config():
    return {
        htypes.cfg_item.typed_cfg_item: resolve_typed_cfg_item,
        }


def typed_cfg_value_config():
    return {
        htypes.cfg_item.typed_cfg_item: resolve_typed_cfg_value,
        }
