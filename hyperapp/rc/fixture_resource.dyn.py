from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_resource import Resource
from .code.system_probe import ConfigFixture


# Config fixtures return resolved configs, which are NOT passed to subprocesses.
class ConfigFixtureResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.service_params)

    def __init__(self, service_name, function, service_params):
        self._service_name = service_name
        self._function = function  # piece
        self._service_params = service_params

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._service_name == rhs._service_name
            and self._function == rhs._function
            and self._service_params == rhs._service_params
            )

    def __hash__(self):
        return hash(('config-fixture-resource', self._service_name, self._function, self._service_params))

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


# Config tempate fixtures return unresolved config templates, with ARE passed to subprocesses.
class ConfigTemplateFixtureResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, web.summon(piece.function), piece.service_params)

    def __init__(self, service_name, function, service_params):
        self._service_name = service_name
        self._function = function  # piece
        self._service_params = service_params

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._service_name == rhs._service_name
            and self._function == rhs._function
            and self._service_params == rhs._service_params
            )

    def __hash__(self):
        return hash(('config-fixture-resource', self._service_name, self._function, self._service_params))

    @property
    def piece(self):
        return htypes.fixture_resource.config_template_fixture_resource(
            service_name=self._service_name,
            function=mosaic.put(self._function),
            service_params=tuple(self._service_params),
            )

    def configure_system(self, system):
        fn = pyobj_creg.animate(self._function)
        service_args = [
            system.resolve_service(name)
            for name in self._service_params
            ]
        config_template = fn(*service_args)
        system.default_layer.update(self._service_name, config_template)
