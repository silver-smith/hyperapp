from . import htypes
from .services import (
    pyobj_creg,
    web,
    )


def resolve_str_cfg_item(piece):
    key = piece.key
    value = web.summon(piece.value)
    return (key, value)


def resolve_typed_cfg_item(piece):
    t = pyobj_creg.invite(piece.t)
    value = web.summon(piece.value)
    return (t, value)


def cfg_item_config():
    return {
        htypes.cfg_item.str_cfg_item: resolve_str_cfg_item,
        htypes.cfg_item.typed_cfg_item: resolve_typed_cfg_item,
        }
