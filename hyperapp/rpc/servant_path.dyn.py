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

    @property
    def title(self):
        return self._name

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

    @property
    def title(self):
        return self._attr_name

    def __str__(self):
        return f"GetAttribute({self._attr_name})"

    def resolve(self, servant):
        return getattr(servant, self._attr_name)


class Partial:

    @classmethod
    def from_piece(cls, piece, mosaic, web):
        param_list = [
            web.summon(ref)
            for ref in piece.params
            ]
        return cls(mosaic, param_list)

    def __init__(self, mosaic, param_list):
        self._mosaic = mosaic
        self._param_list = param_list

    @property
    def piece(self):
        return htypes.servant_path.partial([
            self._mosaic.put(param)
            for param in self._param_list
            ])

    @property
    def title(self):
        return ', '.join(str(p) for p in self._param_list)

    def __str__(self):
        return f"Partial({self._param_list})"

    def resolve(self, fn):
        return partial(fn, *self._param_list)


class ServantPath:

    @classmethod
    def from_data(cls, mosaic, registry, ref_list):
        return cls(mosaic, [
            registry.invite(ref)
            for ref in ref_list
            ])

    def __init__(self, mosaic, path=None):
        self._mosaic = mosaic
        self._path = path or []

    def __str__(self):
        return '/'.join(str(element) for element in self._path)

    @property
    def title(self):
        return '/'.join(element.title for element in self._path)

    def _with_element(self, element):
        return ServantPath(self._mosaic, [*self._path, element])

    def registry_name(self, name):
        return self._with_element(RegistryName(name))

    def get_attr(self, attr_name):
        return self._with_element(GetAttribute(attr_name))

    def partial(self, *args):
        return self._with_element(Partial(self._mosaic, args))

    @property
    def as_data(self):
        return tuple(
            self._mosaic.put(element.piece)
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
        registry.register_actor(htypes.servant_path.partial, Partial.from_piece, services.mosaic, services.web)

        services.servant_path = partial(ServantPath, services.mosaic)
        services.servant_path_from_data = partial(ServantPath.from_data, services.mosaic, registry)
