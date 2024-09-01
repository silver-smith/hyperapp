from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ServiceProbeTemplate


class ServiceProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.service_name, web.summon(piece.function), piece.params)

    def __init__(self, attr_name, service_name, function, params):
        self._attr_name = attr_name
        self._service_name = service_name
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_resource(
            attr_name=self._attr_name,
            service_name=self._service_name,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    def configure_system(self, system):
        fn = pyobj_creg.animate(self._function)
        probe = ServiceProbeTemplate(self._attr_name, fn, self._params)
        system.update_config('system', {self._service_name: probe})
