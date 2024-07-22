from . import htypes
from .services import (
    mosaic,
    )


class ServiceCtr:

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


class Service2Ctr:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_targets(self, resource_target, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        assert 0

    def get_component(self, name_to_res):
        assert 0


class FixtureCtr:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_targets(self, resource_target, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        assert 0

    def get_component(self, name_to_res):
        assert 0
