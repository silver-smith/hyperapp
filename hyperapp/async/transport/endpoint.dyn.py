import logging
import weakref
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


Request = namedtuple('Request', 'receiver_identity sender ref_list')


class TransportLogCallbackRegistry:

    def __init__(self):
        self._weak_method_list = []

    def add(self, fn):
        self._weak_method_list.append(weakref.WeakMethod(fn, self._ref_removed))

    def _ref_removed(self, ref):
        self._weak_method_list.remove(ref)

    def log_transaction(self, direction, ref_list):
        for ref in self._weak_method_list:
            fn = ref()
            if fn is not None:
                fn(direction, ref_list)


class LocalRoute:

    def __init__(self, unbundler, transport_log_callback_registry, identity, endpoint):
        self._unbundler = unbundler
        self._transport_log_callback_registry = transport_log_callback_registry
        self._identity = identity
        self._endpoint = endpoint

    def __repr__(self):
        return f'<async LocalRoute to: {self._endpoint}>'

    @property
    def piece(self):
        return None

    @property
    def available(self):
        return True

    async def send(self, parcel):
        bundle = self._identity.decrypt_parcel(parcel)
        self._unbundler.register_bundle(bundle)
        request = Request(self._identity, parcel.sender, bundle.roots)
        self._transport_log_callback_registry.log_transaction('in', bundle.roots)
        await self._endpoint.process(request)


class EndpointRegistry:

    def __init__(self, mosaic, unbundler, route_table, transport_log_callback_registry):
        self._mosaic = mosaic
        self._unbundler = unbundler
        self._route_table = route_table
        self._transport_log_callback_registry = transport_log_callback_registry

    def register(self, identity, endpoint):
        peer_ref = self._mosaic.put(identity.peer.piece)
        log.info("Local peer %s: %s", ref_repr(peer_ref), endpoint)
        route = LocalRoute(self._unbundler, self._transport_log_callback_registry, identity, endpoint)
        self._route_table.add_route(peer_ref, route)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.transport_log_callback_registry = TransportLogCallbackRegistry()
        services.async_endpoint_registry = EndpointRegistry(
            services.mosaic,
            services.unbundler,
            services.async_route_table,
            services.transport_log_callback_registry,
            )
