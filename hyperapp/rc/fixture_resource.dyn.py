from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ConfigFixture, FixtureObjTemplate, FixtureProbeTemplate


class FixtureObjResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, piece.ctl, web.summon(piece.function), piece.params)

    def __init__(self, service_name, ctl_ref, function, params):
        self._service_name = service_name
        self._ctl_ref = ctl_ref
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.fixture_resource.fixture_obj_resource(
            service_name=self._service_name,
            ctl=self._ctl_ref,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def is_service_resource(self):
        return True

    def configure_system(self, system):
        template = FixtureObjTemplate(self._ctl_ref, self._function, self._params)
        system.update_config('system', {self._service_name: template})


class FixtureProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, piece.ctl, web.summon(piece.function), piece.params)

    def __init__(self, service_name, ctl_ref, function, params):
        self._service_name = service_name
        self._ctl_ref = ctl_ref
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.fixture_resource.fixture_probe_resource(
            service_name=self._service_name,
            ctl=self._ctl_ref,
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def is_service_resource(self):
        return True

    def configure_system(self, system):
        template = FixtureProbeTemplate(self._ctl_ref, self._function, self._params)
        system.update_config('system', {self._service_name: template})


class ConfigFixtureResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.service_params)

    def __init__(self, service_name, function, service_params):
        self._service_name = service_name
        self._function = function  # piece
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.fixture_resource.config_fixture_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            service_params=tuple(self._service_params),
            )

    def configure_system(self, system):
        fixture = ConfigFixture(self._function, self._service_params)
        system.add_item_fixtures(self._service_name, [fixture])
