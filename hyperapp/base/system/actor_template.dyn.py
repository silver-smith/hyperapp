from dataclasses import dataclass

from hyperapp.boot.htypes import Type

from . import htypes
from .services import (
    pyobj_creg,
    )


@dataclass
class ActorRequester:

    actor_t: Type

    def __str__(self):
        return f"Actor {self.actor_t.full_name}"


class ActorTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            )

    def __init__(self, t, fn, service_params):
        self.t = t
        self._fn = fn
        self._service_params = service_params

    def __repr__(self):
        return f"<ActorTemplate {self._fn}({self._service_params})>"

    @property
    def piece(self):
        return htypes.system.actor_template(
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
        return system.bind_services(fn, self._service_params, requester=ActorRequester(self.t))
