import logging
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


Request = namedtuple('Request', 'receiver_identity sender ref_list')


class LocalRoute:

    def __init__(self, unbundler, thread_pool, identity, endpoint):
        self._unbundler = unbundler
        self._thread_pool = thread_pool
        self._identity = identity
        self._endpoint = endpoint

    def __repr__(self):
        return f'<sync LocalRoute to: {self._endpoint}>'

    @property
    def piece(self):
        return None

    def send(self, parcel):
        bundle = self._identity.decrypt_parcel(parcel)
        self._unbundler.register_bundle(bundle)
        request = Request(self._identity, parcel.sender, bundle.roots)
        self._thread_pool.submit(self._endpoint.process, request)


class EndpointRegistry:

    def __init__(self, mosaic, unbundler, route_table, thread_pool):
        self._mosaic = mosaic
        self._unbundler = unbundler
        self._route_table = route_table
        self._thread_pool = thread_pool

    def register(self, identity, endpoint):
        peer_ref = self._mosaic.put(identity.peer.piece)
        log.info("Local peer %s: %s", ref_repr(peer_ref), endpoint)
        route = LocalRoute(self._unbundler, self._thread_pool, identity, endpoint)
        self._route_table.add_route(peer_ref, route)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix='Endpoint')
        services.on_stop.append(self.stop)
        services.endpoint_registry = EndpointRegistry(services.mosaic, services.unbundler, services.route_table, self._thread_pool)

    def stop(self):
        log.info("Shutdown endpoint thread pool")
        self._thread_pool.shutdown()
        log.info("Endpoint thread pool is shut down")
