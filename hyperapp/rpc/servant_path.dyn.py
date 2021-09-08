import logging
from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class RegistryName:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name)

    def __init__(self, name):
        self._name = name

    @property
    def piece(self):
        return htypes.servant_path.registry_name(self._name)

    def __str__(self):
        return f"RegistryName({self._name})"

    def resolve(self, rpc_endpoint):
        return rpc_endpoint.get_servant(self._name)


class GetAttribute:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name)

    def __init__(self, attr_name):
        self._attr_name = attr_name

    @property
    def piece(self):
        return htypes.servant_path.get_attribute(self._attr_name)

    def __str__(self):
        return f"GetAttribute({self._attr_name})"

    def resolve(self, servant):
        return getattr(servant, self._attr_name)


class ServantPath:

    @classmethod
    def from_data(cls, registry, ref_list):
        return cls([
            registry.invite(ref)
            for ref in ref_list
            ])

    def __init__(self, path=None):
        self._path = path or []

    def __str__(self):
        return '/'.join(str(element) for element in self._path)

    def registry_name(self, name):
        return ServantPath([*self._path, RegistryName(name)])

    def get_attr(self, attr_name):
        return ServantPath([*self._path, GetAttribute(attr_name)])

    def as_data(self, mosaic):
        return tuple(
            mosaic.put(element.piece)
            for element in self._path
            )

    def resolve(self, rpc_endpoint):
        value = rpc_endpoint
        for element in self._path:
            value = element.resolve(value)
            log.debug("Servant resolved: %s -> %r", element, value)
        return value


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._registry = registry = CodeRegistry('servant_path', services.web, services.types)
        registry.register_actor(htypes.servant_path.registry_name, RegistryName.from_piece)
        registry.register_actor(htypes.servant_path.get_attribute, GetAttribute.from_piece)

        services.servant_path = ServantPath
        services.servant_path_from_data = partial(ServantPath.from_data, registry)
