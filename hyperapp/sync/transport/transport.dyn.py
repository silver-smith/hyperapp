import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Transport:

    def __init__(self, mosaic, ref_collector, route_registry, route_table):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._route_registry = route_registry
        self._route_table = route_table

    def send_parcel(self, parcel):
        receiver_peer_ref = self._mosaic.put(parcel.receiver.piece)
        route_list = self._route_table.peer_route_list(receiver_peer_ref)
        if not route_list:
            raise RuntimeError(f"No route for peer {receiver_peer_ref}")
        route, *_ = route_list
        log.info("Send parcel %s by route %s (all routes: %s)", parcel, route, route_list)
        route.send(parcel)

    def send(self, receiver, sender_identity, ref_list):
        log.info("Send ref list %s to %s from %s", ref_list, receiver, sender_identity)
        bundle = self._ref_collector(ref_list).bundle
        parcel = receiver.make_parcel(bundle, sender_identity)
        self.send_parcel(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.transport = Transport(
            services.mosaic, services.ref_collector, services.route_registry, services.route_table)
