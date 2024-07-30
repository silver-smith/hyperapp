from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ConfigItemFixture, FixtureProbeTemplate, ServiceProbeTemplate


class ServiceProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.module_name, piece.attr_name, piece.service_name, web.summon(piece.function), piece.params)

    def __init__(self, module_name, attr_name, service_name, function, params):
        self._module_name = module_name
        self._attr_name = attr_name
        self._service_name = service_name
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_resource(
            module_name=self._module_name,
            attr_name=self._attr_name,
            service_name=self._service_name,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def config_triplets(self):
        fn = pyobj_creg.animate(self._function)
        probe = ServiceProbeTemplate(self._module_name, self._attr_name, fn, self._params)
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


class ConfigItemFixtureResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.service_params)

    def __init__(self, service_name, function, service_params):
        self._service_name = service_name
        self._function = function  # piece
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.service_resource.config_item_fixture_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            service_params=tuple(self._service_params),
            )

    @property
    def config_item_fixtures(self):
        fn = pyobj_creg.animate(self._function)
        fixture = ConfigItemFixture(fn, self._service_params)
        return [(self._service_name, fixture)]
