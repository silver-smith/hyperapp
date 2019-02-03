import logging

from hyperapp.common.util import encode_path
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module
from . import htypes

log = logging.getLogger(__name__)

MODULE_NAME = 'resource_registry'


class ResourceRegistry:

    def __init__(self):
        self._registry = {}

    def register(self, key, locale, resource_ref):
        log.debug('    Resource registry: registering %s %s %s -> %s',
                  locale, ref_repr(key.module_ref), encode_path(key.path), ref_repr(resource_ref))
        self._registry[key, locale] = resource_ref

    def resolve(self, key, locale):
        resource_ref = self._registry.get((key, locale))
        log.debug('    Resource registry: resolved %s %s %s -> %s',
                  locale, ref_repr(key.module_ref), encode_path(key.path),
                  ref_repr(resource_ref))
        return resource_ref


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.resource_registry = ResourceRegistry()
