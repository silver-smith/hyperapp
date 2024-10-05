from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class SystemFnCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            fn_ref=piece.system_fn,
            )

    def __init__(self, t, fn_ref):
        self._t = t
        self._fn_ref = fn_ref

    @property
    def piece(self):
        return htypes.system_fn.cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            system_fn=self._fn_ref,
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        fn_creg = system.resolve_service('system_fn_creg')
        return fn_creg.invite(self._fn_ref)
