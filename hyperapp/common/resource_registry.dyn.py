import logging

from hyperapp.common.util import encode_path
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module
from . import htypes

log = logging.getLogger(__name__)


class ResourceRegistry:

    def __init__(self):
        self._registry = {}

    def register(self, key, locale, resource_ref):
        log.debug('    Resource registry: registering %s %s %s -> %s',
                  locale, ref_repr(key.base_ref), encode_path(key.path), ref_repr(resource_ref))
        self._registry[self._make_resource_key(key, locale)] = resource_ref

    def resolve(self, key, locale):
        resource_ref = self._registry.get(self._make_resource_key(key, locale))
        log.debug('    Resource registry: resolved %s %s %s -> %s',
                  locale, ref_repr(key.base_ref), encode_path(key.path),
                  ref_repr(resource_ref))
        return resource_ref

    @staticmethod
    def _make_resource_key(key, locale):
        return (key.base_ref, tuple(key.path), locale)


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.resource_registry = ResourceRegistry()
