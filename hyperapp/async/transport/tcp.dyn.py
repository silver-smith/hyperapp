import asyncio
import logging
from functools import partial

from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module

from . import htypes
from .tcp import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class Connection:

    def __init__(
            self,
            mosaic,
            ref_collector,
            address,
            reader,
            writer,
            ):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._address = address
        self._reader = reader
        self._writer = writer

    def __repr__(self):
        return f"TCP:{address_to_str(self._address)}"

    async def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        bundle = self._ref_collector([parcel_ref]).bundle
        data = encode_tcp_packet(bundle)
        self._writer.write(data)
        log.info("%s: Parcel is sent: %s", self, ref_repr(parcel_ref))


class Route:

    @classmethod
    def from_piece(cls, piece, client_factory):
        return cls((piece.host, piece.port), client_factory)

    def __init__(self, address, client_factory=None):
        self._client_factory = client_factory  # None for routes produced by this process.
        self._address = address

    def __repr__(self):
        return f'tcp_route({address_to_str(self._address)})'

    @property
    def piece(self):
        host, port = self._address
        return htypes.tcp_transport.route(host, port)

    async def send(self, parcel):
        if not self._client_factory:
            raise RuntimeError(f"Can not send parcel using TCP to myself")
        client = await self._client_factory(self._address)
        await client.send(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._event_loop = services.event_loop
        self._mosaic = services.mosaic
        self._ref_collector = services.ref_collector
        self._address_to_client = {}  # (host, port) -> Connection
        self._connect_lock = asyncio.Lock()
        services.async_route_registry.register_actor(htypes.tcp_transport.route, Route.from_piece, self._client_factory)

    async def _client_factory(self, address):
        log.debug('Async tcp: resolving: %s', address_to_str(address))
        # Use lock to avoid multiple connections to same address established in parallel.
        async with self._connect_lock:
            connection = self._address_to_client.get(address)
            if connection:
                log.info('Async tcp: reusing connection %s for %s', connection, address_to_str(address))
                return connection
            log.info('Async tcp: establishing connection for %s', address_to_str(address))
            host, port = address
            reader, writer = await asyncio.open_connection(host, port)
            connection = Connection(
                self._mosaic,
                self._ref_collector,
                address,
                reader,
                writer,
                )
            self._address_to_client[address] = connection
            log.debug('Async tcp: connection for %s is established', address_to_str(address))
            return connection
