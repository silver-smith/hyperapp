from collections import namedtuple

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )


MultiActorItem = namedtuple('MultiActorItem', 'k t fn')


class MultiActorTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            k=web.summon(piece.k),
            t=pyobj_creg.invite(piece.t),
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            )

    def __init__(self, k, t, fn, service_params):
        self._k = k
        self.t = t
        self._fn = fn
        self._service_params = service_params

    def __repr__(self):
        return f"<MultiActorTemplate {self._k}: {self._fn}({self._service_params})>"

    @property
    def piece(self):
        return htypes.system.multi_actor_template(
            k=mosaic.put(self._k),
            t=pyobj_creg.actor_to_ref(self.t),
            function=pyobj_creg.actor_to_ref(self._fn),
            service_params=tuple(self._service_params),
            )

    @property
    def key(self):
        return self.t

    def resolve(self, system, service_name):
        return self._resolve_services(self._fn, system)

    def _resolve_services(self, fn, system):
        if not self._service_params:
            return fn
        service_kw = {
            name: system.resolve_service(name, requester=ActorRequester(self.t))
            for name in self._service_params
            }
        bound_fn = partial(fn, **service_kw)
        return MultiActorItem(self._k, self.t, bound_fn)
