import logging
from collections import defaultdict

from .services import (
    bundler,
    mark,
    mosaic,
    route_registry,
    route_table,
    )
log = logging.getLogger(__name__)


class Transport:

    def __init__(self):
        self._receiver_peer_to_seen_refs = defaultdict(set)

    def send_parcel(self, parcel):
        receiver_peer_ref = mosaic.put(parcel.receiver.piece)
        route_list = route_table.peer_route_list(receiver_peer_ref)
        log.debug("Routes to %s for %s: %s", receiver_peer_ref, parcel, route_list)
        if not route_list:
            raise RuntimeError(f"No route for peer {receiver_peer_ref}")
        route, *_ = [route for route in route_list if route.available]
        log.debug("Send parcel %s by route %s (all routes: %s)", parcel, route, route_list)
        route.send(parcel)

    def send(self, receiver, sender_identity, ref_list):
        log.debug("Send ref list %s to %s from %s", ref_list, receiver, sender_identity)
        seen_refs = self._receiver_peer_to_seen_refs[receiver.piece]
        refs_and_bundle = bundler(ref_list, seen_refs)
        seen_refs |= refs_and_bundle.ref_set
        parcel = receiver.make_parcel(refs_and_bundle.bundle, sender_identity)
        self.send_parcel(parcel)



@mark.service
def transport():
    return Transport()
