import logging
from collections import defaultdict

from hyperapp.common.ref import ref_repr
from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class RouteTable:

    def __init__(self):
        self._peer2route = defaultdict(list)  # ref -> route list

    def add_route(self, peer_ref, route):
        self._peer2route[peer_ref].append(route)

    def peer_route_list(self, peer_ref):
        return self._peer2route[peer_ref]


class Transport:

    def __init__(self, mosaic, ref_collector_factory, route_registry, route_table):
        self._mosaic = mosaic
        self._ref_collector_factory = ref_collector_factory
        self._route_registry = route_registry
        self._route_table = route_table

    def send_parcel(self, parcel):
        receiver_peer_ref = self._mosaic.put(parcel.receiver.piece)
        route_list = self._route_table.peer_route_list(receiver_peer_ref)
        if not route_list:
            raise RuntimeError(f"No route for peer {ref_repr(receiver_peer_ref)}")
        route, *_ = route_list
        log.info("Send parcel %s by route %s", parcel, route)
        route.send(parcel)

    def send(self, receiver, sender_identity, ref_list):
        log.info("Send ref list %s to %s from %s", [ref_repr(ref) for ref in ref_list], receiver, sender_identity)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle(ref_list)
        parcel = receiver.make_parcel(bundle, sender_identity)
        self.send_parcel(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._peer_registry = services.peer_registry
        self._route_table = RouteTable()
        services.route_registry = CodeRegistry('route', services.web, services.types)  # Unused for now.
        services.route_table = self._route_table
        services.transport = Transport(
            services.mosaic, services.ref_collector_factory, services.route_registry, services.route_table)
        services.aux_ref_collector_hooks.append(self.route_collector_hook)

    def route_collector_hook(self, t, ref, value):
        if self._peer_registry.type_registered(t):
            for route in self._route_table.peer_route_list(ref):
                yield self._mosaic.put(route.piece)
