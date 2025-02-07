from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )


class TypedCfgItem:

    @classmethod
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


class TypedFnCfgItem:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            system_fn=web.summon(piece.system_fn),
            )

    def __init__(self, t, system_fn):
        self._t = t
        self._system_fn = system_fn

    @property
    def piece(self):
        return htypes.cfg_item.typed_fn_cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            system_fn=mosaic.put(self._system_fn),
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return system_fn_creg.animate(self._system_fn)
