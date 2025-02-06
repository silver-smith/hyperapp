from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


class TypedCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            value=web.summon(piece.value),
            )

    def __init__(self, t, value):
        self._t = t
        self._value = value

    @property
    def piece(self):
        return htypes.cfg_item.typed_cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            value=mosaic.put(self._value),
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        return self._value
