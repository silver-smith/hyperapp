from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ActorProbeTemplate


class ActorProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            function=web.summon(piece.function),
            params=piece.params,
            )


    def __init__(self, attr_qual_name, service_name, t, function, params):
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._t = t
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.actor_probe_resource(
            attr_qual_name=self._attr_qual_name,
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    def configure_system(self, system):
        fn = pyobj_creg.animate(self._function)
        probe = ActorProbeTemplate(self._attr_qual_name, self._service_name, self._t, fn, self._params)
        system.update_config(self._service_name, {self._t: probe})
