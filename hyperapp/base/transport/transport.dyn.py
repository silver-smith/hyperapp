import logging
from collections import defaultdict

log = logging.getLogger(__name__)


class RemoteIsGoneError(Exception):
    pass


class Transport:

    def __init__(self, bundler, route_table):
        self._bundler = bundler
        self._route_table = route_table
        self._receiver_peer_to_seen_refs = defaultdict(set)

    def send_parcel(self, parcel):
        route_list = self._route_table.peer_route_list(parcel.receiver)
        log.debug("Routes to %s for %s: %s", parcel.receiver, parcel, route_list)
        if not route_list:
            raise RuntimeError(f"No route for peer {parcel.receiver}")
        available_route_list = [route for route in route_list if route.available]
        if not available_route_list:
            raise RuntimeError(f"No available route for peer {parcel.receiver}")
        route, *_ = available_route_list
        log.debug("Send parcel %s by route %s (all routes: %s)", parcel, route, route_list)
        route.send(parcel)

    def send(self, receiver, sender_identity, ref_list):
        log.debug("Send ref list %s to %s from %s", ref_list, receiver, sender_identity)
        seen_refs = self._receiver_peer_to_seen_refs[receiver.piece]
        refs_and_bundle = self._bundler(ref_list, seen_refs)
        seen_refs |= refs_and_bundle.ref_set
        parcel = receiver.make_parcel(refs_and_bundle.bundle, sender_identity)
        self.send_parcel(parcel)


def transport(bundler, route_table):
    return Transport(bundler, route_table)
