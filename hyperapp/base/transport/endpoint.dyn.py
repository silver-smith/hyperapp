import logging
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from hyperapp.boot.ref import ref_repr

from .services import (
    unbundler,
    )

log = logging.getLogger(__name__)


Request = namedtuple('Request', 'receiver_identity remote_peer ref_list')


class LocalRoute:

    def __init__(self, system_failed, transport_log, endpoint_thread_pool, identity, endpoint):
        self._system_failed = system_failed
        self._transport_log = transport_log
        self._endpoint_thread_pool = endpoint_thread_pool
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
        self._transport_log.commit_in_message(parcel, bundle)
        request = Request(self._identity, parcel.sender, bundle.roots)
        self._endpoint_thread_pool.submit(self._process_endpoint, request)

    def _process_endpoint(self, request):
        log.info("Endpoint %s: process request: %s", self._endpoint, request)
        try:
            self._endpoint.process(request)
            log.info("Endpoint %s: done processing request: %s", self._endpoint, request)
        except Exception as x:
            log.exception("Endpoint %s: Error processing request: %s", self._endpoint, request)
            self._system_failed(f"Error in endpoint {self._endpoint} process", x)


class EndpointRegistry:

    def __init__(self, system_failed, transport_log, endpoint_thread_pool, route_table):
        self._system_failed = system_failed
        self._transport_log = transport_log
        self._endpoint_thread_pool = endpoint_thread_pool
        self._route_table = route_table

    def register(self, identity, endpoint):
        log.info("Local peer %s: %s", identity.peer, endpoint)
        route = LocalRoute(self._system_failed, self._transport_log, self._endpoint_thread_pool, identity, endpoint)
        self._route_table.add_route(identity.peer, route)


def endpoint_thread_pool():
    thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix='Endpoint')
    yield thread_pool
    log.info("Shutdown endpoint thread pool")
    thread_pool.shutdown()
    log.info("Endpoint thread pool is shut down")


def endpoint_registry(system_failed, route_table, transport_log, endpoint_thread_pool):
    return EndpointRegistry(system_failed, transport_log, endpoint_thread_pool, route_table)
