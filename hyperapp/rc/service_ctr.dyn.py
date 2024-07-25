from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_constructor import Constructor
from .code.service_resource import FixtureProbeResource, ServiceProbeResource


class ServiceCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_targets(self, resource_target, target_set):
        service_found_tgt = target_set.factory.service_found(self._name)
        service_found_tgt.set_provider(resource_target, self, target_set)
        target_set.update_deps_for(service_found_tgt)

    def make_component(self, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        service = htypes.builtin.call(
            function=mosaic.put(attribute),
            )
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'{self._name}.service'] = service
        return service

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.service']


class ServiceProbeCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name, piece.params)

    def __init__(self, attr_name, name, params):
        self._attr_name = attr_name
        self._name = name
        self._params = params

    def update_targets(self, resource_target, target_set):
        resource_target.import_alias_tgt.add_component(self)

    def make_component(self, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def get_component(self, name_to_res):
        assert 0

    def make_resource(self, module_name, python_module):
        return ServiceProbeResource(module_name, self._attr_name, self._name, self.make_component(python_module), self._params)


class ServiceTemplateCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name, piece.params)

    def __init__(self, attr_name, name, params):
        self._attr_name = attr_name
        self._name = name
        self._params = params

    def update_targets(self, resource_target, target_set):
        resource_target.import_alias_tgt.add_component(self)

    def make_component(self, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        service = htypes.builtin.call(
            function=mosaic.put(attribute),
            )
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'{self._name}.service'] = service
        return service

    def get_component(self, name_to_res):
        assert 0


class FixtureCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name, piece.params)

    def __init__(self, attr_name, name, params):
        self._attr_name = attr_name
        self._name = name
        self._params = params

    def update_tests_targets(self, import_alias_tgt, target_set):
        import_alias_tgt.add_component(self)

    def make_component(self, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def get_component(self, name_to_res):
        assert 0

    def make_resource(self, module_name, python_module):
        return FixtureProbeResource(self._name, self.make_component(python_module), self._params)
