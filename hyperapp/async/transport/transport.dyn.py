import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Transport:

    def __init__(self, mosaic, ref_collector, route_registry, route_table, transport_log_callback_registry):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._route_registry = route_registry
        self._route_table = route_table
        self._transport_log_callback_registry = transport_log_callback_registry

    async def send_parcel(self, parcel):
        receiver_peer_ref = self._mosaic.put(parcel.receiver.piece)
        route_list = self._route_table.peer_route_list(receiver_peer_ref)
        if not route_list:
            raise RuntimeError(f"No route for peer {receiver_peer_ref}")
        route, *_ = [route for route in route_list if route.available]
        log.info("Send parcel %s by route %s", parcel, route)
        await route.send(parcel)

    async def send(self, receiver, sender_identity, ref_list):
        log.info("Send ref list %s to %s from %s", ref_list, receiver, sender_identity)
        self._transport_log_callback_registry.log_transaction('out', ref_list)
        bundle = self._ref_collector(ref_list).bundle
        parcel = receiver.make_parcel(bundle, sender_identity)
        await self.send_parcel(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.async_transport = Transport(
            services.mosaic,
            services.ref_collector,
            services.async_route_registry,
            services.async_route_table,
            services.transport_log_callback_registry,
            )
