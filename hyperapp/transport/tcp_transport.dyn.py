import logging
import selectors
import socket
import threading
from functools import partial

from . import htypes
from .services import (
    bundler,
    failed,
    mark,
    mosaic,
    on_stop,
    parcel_registry,
    route_table,
    transport,
    stop_signal,
    unbundler,
    )
from .code.tcp_utils import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class Server:

    def __init__(self, selector, connection_factory):
        self._selector = selector
        self._connection_factory = connection_factory
        self._listen_socket = socket.socket()
        self._actual_address = None
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __repr__(self):
        return f"<sync tcp Server:{address_to_str(self._actual_address)}>"

    def start(self, bind_address):
        self._listen_socket.bind(bind_address or ('localhost', 0))
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

    def __init__(self, selector, address, sock):
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
        parcel_ref = mosaic.put(parcel.piece)
        bundle = bundler([parcel_ref]).bundle
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
        unbundler.register_bundle(bundle)
        parcel = parcel_registry.invite(parcel_ref)
        sender_ref = mosaic.put(parcel.sender.piece)
        # Add route first - it may be used during parcel processing.
        log.info("%s will be routed via established connection from: %s", sender_ref, self)
        route_table.add_route(sender_ref, self._this_route)
        transport.send_parcel(parcel)


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

    @property
    def available(self):
        return self._client_factory is not None

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

    @property
    def available(self):
        return True

    def send(self, parcel):
        if self._connection.closed:
            raise RuntimeError(f"Can not send {parcel} back to {self._connection}: it is already closed")
        self._connection.send(parcel)


def selector_thread_main(selector, address_to_client):
    log.info("TCP selector thread is started.")
    try:
        while not stop_signal.is_set():
            event_list = selector.select(timeout=0.5)
            for key, mask in event_list:
                handler = key.data
                handler(key.fileobj, mask)
            for address, client in address_to_client.items():
                if client.closed:
                    log.debug("Remove client %s from cache", client)
                    del address_to_client[address]
    except Exception as x:
        log.exception("TCP selector thread is failed:")
        failed(f"TCP selector thread is failed: {x}", x)
    log.info("TCP selector thread is finished.")


@mark.service
def tcp_server_factory():
    selector = selectors.DefaultSelector()
    address_to_client = {}  # (host, port) -> Connection
    selector_thread = threading.Thread(target=selector_thread_main(selector, address_to_client))

    def stop():
        log.info("Stop TCP selector thread.")
        selector_thread.join()
        log.info("TCP selector thread is stopped.")

    def connection_factory(address, sock):
        sock.setblocking(False)
        return Connection(selector, address, sock)

    def client_factory(address):
        connection = address_to_client.get(address)
        if not connection:
            sock = socket.socket()
            sock.connect(address)
            connection = connection_factory(address, sock)
            address_to_client[address] = connection
            selector.register(sock, selectors.EVENT_READ, connection.on_read)
        return connection

    def server_factory(bind_address=None):
        server = Server(selector, connection_factory)
        server.start(bind_address)
        return server

    route_registry.register_actor(htypes.tcp_transport.route, Route.from_piece, client_factory)
    selector_thread.start()
    on_stop.append(stop)
    return server_factory
