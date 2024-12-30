from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark


class ViewCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            system_fn=web.summon(piece.system_fn),
            )

    def __init__(self, t, system_fn):
        self._t = t
        self._system_fn = system_fn

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return system_fn_creg.animate(self._system_fn)
