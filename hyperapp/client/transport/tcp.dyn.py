import logging
import asyncio

from hyperapp.common.interface import hyper_ref as href_types
from hyperapp.common.interface import tcp_transport as tcp_transport_types
from hyperapp.common.ref import ref_repr, decode_capsule
from hyperapp.common.visual_rep import pprint
from hyperapp.common.tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.tcp'
TCP_PACKET_ENCODING = 'cdr'


class TcpProtocol(asyncio.Protocol):

    def __init__(self, event_loop, types, ref_registry, ref_resolver, endpoint_registry, ref_collector_factory, unbundler, remoting, address):
        self._types = types
        self._ref_registry = ref_registry
        self._ref_resolver = ref_resolver
        self._endpoint_registry = endpoint_registry
        self._ref_collector_factory = ref_collector_factory
        self._unbundler = unbundler
        self._remoting = remoting
        self._address = address
        self._recv_buf = b''

    def __str__(self):
        return 'to %s:%d' % (self._address.host, self._address.port)

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
        for root_ref in bundle.roots:
            capsule = self._ref_resolver.resolve_ref(root_ref)
            if capsule.full_type_name == ['hyper_ref', 'rpc_message']:
                self._process_rpc_message(root_ref, capsule)
            else:
                assert False, 'Unexpected capsule type: %r' % '.'.join(capsule.full_type_name)

    def _process_rpc_message(self, rpc_message_ref, rpc_message_capsule):
        rpc_message = decode_capsule(self._types, rpc_message_capsule)
        assert isinstance(rpc_message, href_types.rpc_message), repr(rpc_message)
        self._remoting.process_rpc_message(rpc_message_ref, rpc_message)

    def send(self, message_ref):
        assert isinstance(message_ref, href_types.ref), repr(message_ref)
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
        self._address_to_protocol = {}  # tcp_transport_types.address -> TcpProtocol
        self._connect_lock = asyncio.Lock()
        services.transport_registry.register(
            tcp_transport_types.address,
            self._resolve_address,
            services.types,
            services.ref_registry,
            services.ref_resolver,
            services.endpoint_registry,
            services.ref_collector_factory,
            services.unbundler,
            services.remoting,
            )

    async def _resolve_address(self, address_ref, address, types, ref_registry, ref_resolver, endpoint_registry, ref_collector_factory, unbundler, remoting):
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
                types,
                ref_registry,
                ref_resolver,
                endpoint_registry,
                ref_collector_factory,
                unbundler,
                remoting,
                address,
                )
            asyncio_transport, protocol = await self._event_loop.create_connection(constructor, address.host, address.port)
            self._address_to_protocol[address] = protocol
            log.debug('Tcp transport: connection for %s is established', ref_repr(address_ref))
            return protocol
