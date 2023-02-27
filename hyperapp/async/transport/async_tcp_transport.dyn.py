import asyncio
import logging
from functools import partial

from hyperapp.common.module import Module

from . import htypes
from .tcp_utils import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class Connection:

    def __init__(self, mosaic, bundler, unbundler, parcel_registry, route_table, transport,
                 client_factory, address, reader, writer):
        self._mosaic = mosaic
        self._bundler = bundler
        self._unbundler = unbundler
        self._parcel_registry = parcel_registry
        self._route_table = route_table
        self._transport = transport
        self._client_factory = client_factory
        self._address = address
        self._reader = reader
        self._writer = writer
        self._receive_task = asyncio.create_task(self.receive())

    def __repr__(self):
        return f"<async tcp Connection from: {address_to_str(self._address)}>"

    async def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        bundle = self._bundler([parcel_ref]).bundle
        data = encode_tcp_packet(bundle)
        self._writer.write(data)
        log.info("%s: Parcel is sent: %s", self, parcel_ref)

    async def receive(self):
        log.info("%s: Receive task started", self)
        try:
            buffer = b''
            while True:
                data = await self._reader.read(1024**2)
                buffer += data
                while has_full_tcp_packet(buffer):
                    bundle, packet_size = decode_tcp_packet(buffer)
                    buffer = buffer[packet_size:]
                    await self._process_bundle(bundle)
        except asyncio.CancelledError:
            log.info("%s: Receive task is stopped", self)
        except Exception as x:
            log.exception("%s: Receive task is failed:", self)

    async def _process_bundle(self, bundle):
        parcel_ref = bundle.roots[0]
        log.info("%s: Received bundle: parcel: %s", self, parcel_ref)
        self._unbundler.register_bundle(bundle)
        parcel = self._parcel_registry.invite(parcel_ref)
        sender_ref = self._mosaic.put(parcel.sender.piece)
        # Add route first - it may be used during parcel processing.
        log.info("%s will be routed via %s", sender_ref, self)
        this_route = Route(self._address, self._client_factory)
        self._route_table.add_route(sender_ref, this_route)
        await self._transport.send_parcel(parcel)


class Route:

    @classmethod
    def from_piece(cls, piece, client_factory):
        return cls((piece.host, piece.port), client_factory)

    def __init__(self, address, client_factory=None):
        self._client_factory = client_factory  # None for routes produced by this process.
        self._address = address

    def __repr__(self):
        if self._client_factory:
            suffix = ''
        else:
            suffix = '/local'
        return f"<async tcp Route:{address_to_str(self._address)}{suffix}>"

    @property
    def piece(self):
        host, port = self._address
        return htypes.tcp_transport.route(host, port)

    @property
    def available(self):
        return self._client_factory is not None

    async def send(self, parcel):
        if not self._client_factory:
            raise RuntimeError("Can not send parcel using TCP to myself")
        client = await self._client_factory(self._address)
        await client.send(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        self._bundler = services.bundler
        self._unbundler = services.unbundler
        self._parcel_registry = services.parcel_registry
        self._route_table = services.async_route_table
        self._transport = services.async_transport
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
                self._mosaic, self._bundler, self._unbundler, self._parcel_registry, self._route_table, self._transport,
                self._client_factory, address, reader, writer)
            self._address_to_client[address] = connection
            log.debug('Async tcp: connection for %s is established', address_to_str(address))
            return connection
