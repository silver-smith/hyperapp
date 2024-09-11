from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ServiceProbeTemplate


class ServiceProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece, config_ctl_creg):
        ctl = config_ctl_creg.invite(piece.ctl)
        return cls(piece.attr_name, piece.service_name, ctl, web.summon(piece.function), piece.params)

    def __init__(self, attr_name, service_name, ctl, function, params):
        self._attr_name = attr_name
        self._service_name = service_name
        self._ctl = ctl
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_resource(
            attr_name=self._attr_name,
            service_name=self._service_name,
            ctl=mosaic.put(self._ctl.piece),
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def is_system_resource(self):
        return True

    def configure_system(self, system):
        probe = ServiceProbeTemplate(self._attr_name, self._ctl, self._function, self._params)
        system.update_config('system', {self._service_name: probe})
