from collections import defaultdict

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class RouteAssociationRegistry:

    def __init__(self):
        self._peer2route = defaultdict(list)  # ref -> ref list

    def associate(self, peer_ref, route_ref):
        self._peer2route[peer_ref].append(route_ref)

    def get(self, peer_ref):
        return self._peer2route[peer_ref]


class Transport:

    def __init__(self, route_registry, route_a9n_registry):
        self._route_registry = route_registry
        self._route_a9n_registry = route_a9n_registry

    def send(self, parcel):
        raise NotImplementedError('todo')
        # route_list = self._route_a9n_registry.get(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.route_registry = CodeRegistry('route', services.ref_resolver, services.types)
        services.route_a9n_registry = RouteAssociationRegistry()
        services.transport = Transport(services.route_registry, services.route_a9n_registry)
