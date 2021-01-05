import logging
from collections import defaultdict

from hyperapp.common.ref import ref_repr
from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class RouteAssociationRegistry:

    def __init__(self):
        self._peer2route = defaultdict(list)  # ref -> route list

    def associate(self, peer_ref, route):
        self._peer2route[peer_ref].append(route)

    def peer_route_list(self, peer_ref):
        return self._peer2route[peer_ref]


class Transport:

    def __init__(self, ref_registry, ref_collector_factory, route_registry, route_a9n_registry):
        self._ref_registry = ref_registry
        self._ref_collector_factory = ref_collector_factory
        self._route_registry = route_registry
        self._route_a9n_registry = route_a9n_registry

    def send_parcel(self, parcel):
        receiver_peer_ref = self._ref_registry.distil(parcel.receiver.piece)
        route_list = self._route_a9n_registry.peer_route_list(receiver_peer_ref)
        if not route_list:
            raise RuntimeError(f"No route for peer {ref_repr(receiver_peer_ref)}")
        route, *_ = route_list
        log.info("Sending parcel %s by route %s", parcel, route)
        route.send(parcel)

    def send(self, receiver, sender_identity, ref_list):
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle(ref_list)
        parcel = receiver.make_parcel(bundle, sender_identity)
        self.send_parcel(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.route_registry = CodeRegistry('route', services.ref_resolver, services.types)  # Unused for now.
        services.route_a9n_registry = RouteAssociationRegistry()
        services.transport = Transport(
            services.ref_registry, services.ref_collector_factory, services.route_registry, services.route_a9n_registry)
