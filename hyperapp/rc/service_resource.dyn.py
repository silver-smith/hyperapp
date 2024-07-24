from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ServiceProbe


class ServiceFnResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.params)

    def __init__(self, service_name, function, params):
        self._service_name = service_name
        self._function = function
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_fn_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def config_triplets(self):
        fn = pyobj_creg.animate(self._function)
        probe = ServiceProbe(fn, self._params)
        return [('system', self._service_name, probe)]
