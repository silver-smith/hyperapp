# register capsules and routes from a bundle


import logging

from hyperapp.common.ref import LOCAL_TRANSPORT_REF
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'unbundler'


class Unbundler(object):

    def __init__(self, ref_registry, route_registry):
        self._ref_registry = ref_registry
        self._route_registry = route_registry

    def register_bundle(self, bundle):
        for capsule in bundle.capsule_list:
            self._ref_registry.register_capsule(capsule)
        for route in bundle.route_list:
            if route.transport_ref == LOCAL_TRANSPORT_REF:
                continue  # must be handled by transport
            self._route_registry.register(route)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.unbundler = Unbundler(services.ref_registry, services.route_registry)
