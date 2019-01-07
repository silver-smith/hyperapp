import logging
import asyncio

from hyperapp.common.htypes import ref_t
from hyperapp.common.ref import ref_repr
from hyperapp.common.visual_rep import pprint
from hyperapp.client.module import ClientModule
from .  import htypes
from .tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.tcp'
TCP_PACKET_ENCODING = 'cdr'


class TcpProtocol(asyncio.Protocol):

    def __init__(
            self,
            event_loop,
            ref_resolver,
            type_resolver,
            ref_registry,
            endpoint_registry,
            ref_collector_factory,
            unbundler,
            remoting,
            address_ref,
            address,
            ):
        self._ref_resolver = ref_resolver
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._endpoint_registry = endpoint_registry
        self._ref_collector_factory = ref_collector_factory
        self._unbundler = unbundler
        self._remoting = remoting
        self._address_ref = address_ref
        self._address = address
        self._recv_buf = b''

    def __str__(self):
        return 'to %s %s:%d' % (ref_repr(self._address_ref), self._address.host, self._address.port)

    def connection_made(self, asyncio_transport):
        log.info('tcp connection made')
        self._asyncio_transport = asyncio_transport

    def data_received(self, data):
        self._log('%d bytes is received' % len(data))
        self._recv_buf += data
        while has_full_tcp_packet(self._recv_buf):
            bundle, packet_size = decode_tcp_packet(self._recv_buf)
            self._process_incoming_bundle(bundle)
            assert packet_size <= len(self._recv_buf), repr(packet_size)
            self._recv_buf = self._recv_buf[packet_size:]
            self._log('consumed %d bytes, remained %d' % (packet_size, len(self._recv_buf)))

    def _process_incoming_bundle(self, bundle):
        self._log('Received bundle: refs: %r, %d capsules' % (list(map(ref_repr, bundle.roots)), len(bundle.capsule_list)))
        pprint(bundle, indent=1)
        self._unbundler.register_bundle(bundle)
        for rpc_message_ref in bundle.roots:
            rpc_message = self._type_resolver.resolve_ref_to_data(rpc_message_ref, expected_type=htypes.hyper_ref.rpc_message)
            self._remoting.process_rpc_message(rpc_message_ref, rpc_message)

    def send(self, message_ref):
        assert isinstance(message_ref, ref_t), repr(message_ref)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([message_ref])
        self._log('Sending bundle:')
        pprint(bundle, indent=1)
        data = encode_tcp_packet(bundle, TCP_PACKET_ENCODING)
        self._log('sending data, size=%d' % len(data))
        self._asyncio_transport.write(data)

    def _log(self, message):
        log.info('tcp %s: %s', self, message)
        

class TcpTransport(object):

    def __init__(self, event_loop):
        self._event_loop = event_loop


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._event_loop = services.event_loop
        self._address_to_protocol = {}  # htypes.tcp_transport.address -> TcpProtocol
        self._connect_lock = asyncio.Lock()
        address_type_ref = services.type_resolver.reverse_resolve(htypes.tcp_transport.address)
        services.transport_registry.register_type_ref(
            address_type_ref,
            self._resolve_address,
            services.ref_resolver,
            services.type_resolver,
            services.ref_registry,
            services.endpoint_registry,
            services.ref_collector_factory,
            services.unbundler,
            services.remoting,
            )

    async def _resolve_address(
            self,
            address_ref,
            address,
            ref_resolver,
            type_resolver,
            ref_registry,
            endpoint_registry,
            ref_collector_factory,
            unbundler,
            remoting,
            ):
        log.debug('Tcp transport: resolving address %s: %s', ref_repr(address_ref), address)
        # use lock to avoid multiple connections to same address established in parallel
        with (await self._connect_lock):
            protocol = self._address_to_protocol.get(address)
            if protocol:
                log.info('Tcp transport: reusing connection %s for %s', protocol, ref_repr(address_ref))
                return protocol
            log.info('Tcp transport: establishing connection for %s', ref_repr(address_ref))
            constructor = lambda: TcpProtocol(
                self._event_loop,
                ref_resolver,
                type_resolver,
                ref_registry,
                endpoint_registry,
                ref_collector_factory,
                unbundler,
                remoting,
                address_ref,
                address,
                )
            asyncio_transport, protocol = await self._event_loop.create_connection(constructor, address.host, address.port)
            self._address_to_protocol[address] = protocol
            log.debug('Tcp transport: connection for %s is established', ref_repr(address_ref))
            return protocol
