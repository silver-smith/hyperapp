import logging

from hyperapp.common.util import encode_path
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module
from . import htypes

log = logging.getLogger(__name__)


class ResourceResolver:

    def __init__(self, type_resolver, resource_registry):
        self._type_resolver = type_resolver
        self._resource_registry = resource_registry

    def resolve(self, key, locale, expected_type=None):
        resource_ref = self._resource_registry.resolve(key, locale)
        if not resource_ref:
            return None
        return self._type_resolver.resolve_ref(resource_ref, expected_type).value


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.resource_resolver = ResourceResolver(services.type_resolver, services.resource_registry)
