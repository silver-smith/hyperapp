import logging
import selectors
import socket
import struct
import threading

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


# utf-8 encoded encoding size, packet data size
STRUCT_FORMAT = '!QQ'
TCP_BUNDLE_ENCODING = 'cdr'


def address_to_str(address):
    host, port = address
    return f'{host}:{port}'


def has_full_tcp_packet(data):
    header_size = struct.calcsize(STRUCT_FORMAT)
    if len(data) < header_size:
        return False
    encoding_size, size = struct.unpack(STRUCT_FORMAT, data[:header_size])
    return len(data) >= header_size + encoding_size + size


def decode_tcp_packet(data):
    assert has_full_tcp_packet(data)
    header_size = struct.calcsize(STRUCT_FORMAT)
    encoding_size, size = struct.unpack(STRUCT_FORMAT, data[:header_size])
    encoding = data[header_size:header_size + encoding_size].decode()
    packet_data = data[header_size + encoding_size:header_size + encoding_size + size]
    bundle = packet_coders.decode(encoding, packet_data, bundle_t)
    return (bundle, header_size + encoding_size + size)


def encode_tcp_packet(bundle, encoding):
    assert isinstance(bundle, bundle_t), repr(bundle)
    packet_data = packet_coders.encode(encoding, bundle)
    encoded_encoding = encoding.encode()
    header = struct.pack(STRUCT_FORMAT, len(encoded_encoding), len(packet_data))
    return header + encoded_encoding + packet_data


class Server:

    def __init__(self, selector):
        self._selector = selector
        self._socket = socket.socket()
        self._actual_address = None

    def start(self, bind_address):
        self._socket.bind(bind_address)
        self._socket.listen(100)
        self._socket.setblocking(False)
        self._selector.register(self._socket, selectors.EVENT_READ, self._on_accept)
        self._actual_address = self._socket.getsockname()
        log.info("Listening on %s", address_to_str(self._actual_address))

    @property
    def route(self):
        return Route(self._actual_address)

    def _on_accept(self, listen_sock, mask):
        sock, address = listen_sock.accept()
        log.info("Accepted connection from %s", address_to_str(address))
        raise NotImplementedError('todo')


class Client:

    def __init__(self, mosaic, ref_collector_factory, selector, address):
        self._mosaic = mosaic
        self._ref_collector_factory = ref_collector_factory
        self._selector = selector
        self._address = address
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect(address)

    def __repr__(self):
        return f"TCP:{address_to_str(self._address)}"

    def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([parcel_ref])
        data = encode_tcp_packet(bundle, TCP_BUNDLE_ENCODING)
        ofs = 0
        while ofs < len(data):
            sent_size = self._socket.send(data[ofs:])
            log.debug("%s: sent %d bytes", self, sent_size)
            if sent_size == 0:
                raise RuntimeError(f"{self}: remote end closed connection")
            ofs += sent_size
        log.info("%s: parcel is sent: %s", self, ref_repr(parcel_ref))


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

    def send(self, parcel):
        if not self._client_factory:
            raise RuntimeError(f"Can not send parcel using TCP to myself")
        client = self._client_factory(self._address)
        client.send(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._ref_collector_factory = services.ref_collector_factory
        self._on_failure = services.failed
        self._stop_flag = False
        self._selector = selectors.DefaultSelector()
        self._address_to_client = {}
        self._thread = threading.Thread(target=self._selector_thread_main)
        services.route_registry.register_actor(htypes.tcp_transport.route, Route.from_piece, self._client_factory)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)
        services.tcp_server = self.server_factory

    def server_factory(self, bind_address):
        server = Server(self._selector)
        server.start(bind_address)
        return server

    def _client_factory(self, address):
        client = self._address_to_client.get(address)
        if not client:
            client = Client(self._mosaic, self._ref_collector_factory, self._selector, address)
            self._address_to_client[address] = client
        return client

    def start(self):
        log.info("Start TCP selector thread.")
        self._thread.start()

    def stop(self):
        log.info("Stop TCP selector thread.")
        self._stop_flag = True
        self._thread.join()
        log.info("TCP selector thread is stopped.")

    def _selector_thread_main(self):
        log.info("TCP selector thread is started.")
        try:
            while not self._stop_flag:
                event_list = self._selector.select(timeout=0.5)
                for key, mask in event_list:
                    handler = key.data
                    handler(key.fileobj, mask)
        except Exception as x:
            log.exception("TCP selector thread is failed:")
            self._on_failure(f"TCP selector thread is failed: {x}", x)
        log.info("TCP selector thread is finished.")
