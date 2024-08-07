import logging
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from hyperapp.common.ref import ref_repr

from .services import (
    failed,
    mark,
    mosaic,
    on_stop,
    unbundler,
    )

log = logging.getLogger(__name__)


Request = namedtuple('Request', 'receiver_identity sender ref_list')


class LocalRoute:

    def __init__(self, identity, endpoint):
        self._identity = identity
        self._endpoint = endpoint

    def __repr__(self):
        return f'<sync LocalRoute to: {self._endpoint}>'

    @property
    def piece(self):
        return None

    @property
    def available(self):
        return True

    def send(self, parcel):
        parcel.verify()
        bundle = self._identity.decrypt_parcel(parcel)
        unbundler.register_bundle(bundle)
        request = Request(self._identity, parcel.sender, bundle.roots)
        _thread_pool.submit(self._process_endpoint, request)

    def _process_endpoint(self, request):
        try:
            self._endpoint.process(request)
        except Exception as x:
            log.exception("Error processing endpoint %s:", self._endpoint)
            failed(f"Error in endpoint {self._endpoint} process", x)


class EndpointRegistry:

    def __init__(self, route_table):
        self._route_table = route_table

    def register(self, identity, endpoint):
        peer_ref = mosaic.put(identity.peer.piece)
        log.info("Local peer %s: %s", ref_repr(peer_ref), endpoint)
        route = LocalRoute(identity, endpoint)
        self._route_table.add_route(peer_ref, route)


def endpoint_registry(route_table):
    return EndpointRegistry(route_table)


def stop():
    log.info("Shutdown endpoint thread pool")
    _thread_pool.shutdown()
    log.info("Endpoint thread pool is shut down")


_thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix='Endpoint')
on_stop.append(stop)
