from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import FixtureProbeTemplate, ServiceProbeTemplate


class ServiceProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.params)

    def __init__(self, service_name, function, params):
        self._service_name = service_name
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def config_triplets(self):
        fn = pyobj_creg.animate(self._function)
        probe = ServiceProbeTemplate(fn, self._params)
        return [('system', self._service_name, probe)]


class FixtureProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.params)

    def __init__(self, service_name, function, params):
        self._service_name = service_name
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.fixture_probe_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def config_triplets(self):
        fn = pyobj_creg.animate(self._function)
        probe = FixtureProbeTemplate(fn, self._params)
        return [('system', self._service_name, probe)]


class ServiceTemplateResource(Resource):

    @classmethod
    def from_template(cls, service_name, template):
        return cls(
            service_name=service_name,
            function=pyobj_creg.actor_to_ref(template.fn),
            free_params=template.free_params,
            service_params=template.service_params,
            want_config=template.want_config,
            )
            
    @classmethod
    def from_piece(cls, piece):
        return cls(
            service_name=piece.service_name,
            function=web.summon(piece.function),
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, service_name, function, free_params, service_params, want_config):
        self._service_name = service_name
        self._function = function  # piece
        self._free_params = free_params
        self._service_params = service_params
        self._want_config = want_config

    @property
    def piece(self):
        return htypes.service_resource.service_template_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            free_params=tuple(self._free_params),
            service_params=tuple(self._service_params),
            want_config=self._want_config
            )
