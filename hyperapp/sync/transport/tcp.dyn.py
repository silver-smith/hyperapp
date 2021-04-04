import logging
import selectors
import socket
import threading

from hyperapp.common.module import Module

from . import htypes
from .tcp import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class Server:

    def __init__(self, selector, connection_factory):
        self._selector = selector
        self._connection_factory = connection_factory
        self._listen_socket = socket.socket()
        self._actual_address = None

    def __repr__(self):
        return f"<sync tcp Server:{address_to_str(self._actual_address)}>"

    def start(self, bind_address):
        self._listen_socket.bind(bind_address)
        self._listen_socket.listen(100)
        self._listen_socket.setblocking(False)
        self._selector.register(self._listen_socket, selectors.EVENT_READ, self._on_accept)
        self._actual_address = self._listen_socket.getsockname()
        log.info("%s: Listening.", self)

    @property
    def route(self):
        return Route(self._actual_address)

    def _on_accept(self, listen_sock, mask):
        sock, address = listen_sock.accept()
        log.info("%s: Accepted connection from %s", self, address_to_str(address))
        sock.setblocking(False)
        connection = self._connection_factory(address, sock)
        self._selector.register(sock, selectors.EVENT_READ, connection.on_read)


class Connection:

    def __init__(self, mosaic, ref_collector, unbundler, parcel_registry,
                 route_table, transport, selector, address, sock):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._unbundler = unbundler
        self._parcel_registry = parcel_registry
        self._route_table = route_table
        self._transport = transport
        self._selector = selector
        self._address = address
        self._socket = sock
        self._buffer = b''
        self._this_route = IncomingConnectionRoute(self)

    def __repr__(self):
        return f"<sync tcp Connection from: {address_to_str(self._address)}>"

    @property
    def closed(self):
        return self._socket is None

    def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        bundle = self._ref_collector([parcel_ref]).bundle
        data = encode_tcp_packet(bundle)
        ofs = 0
        while ofs < len(data):
            sent_size = self._socket.send(data[ofs:])
            log.debug("%s: Sent %d bytes", self, sent_size)
            if sent_size == 0:
                raise RuntimeError(f"{self}: remote end closed connection")
            ofs += sent_size
        log.info("%s: Parcel is sent: %s", self, parcel_ref)

    def on_read(self, sock, mask):
        try:
            data = sock.recv(1024**2)
        except ConnectionResetError as x:
            log.warning("%s: Remote end reset connection: %s", self, x)
        else:
            if data == b'':
                log.info("%s: Remote end closed connection", self)
            else:
                self._buffer += data
                self._process_buffer()
                return
        self._selector.unregister(sock)
        self._socket = None

    def _process_buffer(self):
        while has_full_tcp_packet(self._buffer):
            bundle, packet_size = decode_tcp_packet(self._buffer)
            self._buffer = self._buffer[packet_size:]
            self._process_bundle(bundle)

    def _process_bundle(self, bundle):
        parcel_ref = bundle.roots[0]
        log.info("%s: Received bundle: parcel: %s", self, parcel_ref)
        self._unbundler.register_bundle(bundle)
        parcel = self._parcel_registry.invite(parcel_ref)
        sender_ref = self._mosaic.put(parcel.sender.piece)
        # Add route first - it may be used during parcel processing.
        log.info("%s will be routed via established connection from: %s", sender_ref, self)
        self._route_table.add_route(sender_ref, self._this_route)
        self._transport.send_parcel(parcel)


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
        return f"<sync tcp Route:{address_to_str(self._address)}{suffix}>"

    @property
    def piece(self):
        host, port = self._address
        return htypes.tcp_transport.route(host, port)

    def send(self, parcel):
        if not self._client_factory:
            raise RuntimeError("Can not send parcel using TCP to myself")
        client = self._client_factory(self._address)
        client.send(parcel)


class IncomingConnectionRoute:

    def __init__(self, connection):
        self._connection = connection

    @property
    def piece(self):
        return None  # Not persistable.

    def send(self, parcel):
        if self._connection.closed:
            raise RuntimeError(f"Can not send {parcel} back to {self._connection}: it is already closed")
        self._connection.send(parcel)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._ref_collector = services.ref_collector
        self._unbundler = services.unbundler
        self._parcel_registry = services.parcel_registry
        self._route_table = services.route_table
        self._transport = services.transport
        self._on_failure = services.failed
        self._stop_flag = False
        self._selector = selectors.DefaultSelector()
        self._address_to_client = {}  # (host, port) -> Connection
        self._thread = threading.Thread(target=self._selector_thread_main)
        services.route_registry.register_actor(htypes.tcp_transport.route, Route.from_piece, self._client_factory)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)
        services.tcp_server = self.server_factory

    def server_factory(self, bind_address=('localhost', 0)):
        server = Server(self._selector, self._connection_factory)
        server.start(bind_address)
        return server

    def _client_factory(self, address):
        connection = self._address_to_client.get(address)
        if not connection:
            sock = socket.socket()
            sock.connect(address)
            connection = self._connection_factory(address, sock)
            self._address_to_client[address] = connection
            self._selector.register(sock, selectors.EVENT_READ, connection.on_read)
        return connection

    def _connection_factory(self, address, sock):
        sock.setblocking(False)
        return Connection(
            self._mosaic,
            self._ref_collector,
            self._unbundler,
            self._parcel_registry,
            self._route_table,
            self._transport,
            self._selector,
            address,
            sock,
            )

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
                for address, client in self._address_to_client.items():
                    if client.closed:
                        log.debug("Remove client %s from cache", client)
                        del self._address_to_client[address]
        except Exception as x:
            log.exception("TCP selector thread is failed:")
            self._on_failure(f"TCP selector thread is failed: {x}", x)
        log.info("TCP selector thread is finished.")
