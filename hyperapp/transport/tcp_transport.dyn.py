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
    route_registry,
    route_table,
    transport,
    stop_signal,
    unbundler,
    )
from .code.tcp_utils import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class Server:

    def __init__(self):
        self._listen_socket = socket.socket()
        self._actual_address = None
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __repr__(self):
        return f"<sync tcp Server:{address_to_str(self._actual_address)}>"

    def start(self, bind_address=None):
        self._listen_socket.bind(bind_address or ('localhost', 0))
        self._listen_socket.listen(100)
        self._listen_socket.setblocking(False)
        _selector.register(self._listen_socket, selectors.EVENT_READ, self._on_accept)
        self._actual_address = self._listen_socket.getsockname()
        log.info("%s: Listening.", self)

    @property
    def route(self):
        return Route(self._actual_address, is_local=True)

    def _on_accept(self, listen_sock, mask):
        sock, address = listen_sock.accept()
        log.info("%s: Accepted connection from %s", self, address_to_str(address))
        sock.setblocking(False)
        connection = Connection(address, sock)
        _selector.register(sock, selectors.EVENT_READ, connection.on_read)


class Connection:

    def __init__(self, address, sock):
        self._address = address
        self._socket = sock
        self._buffer = b''
        self._this_route = IncomingConnectionRoute(self)
        self._seen_refs = set()

    def __repr__(self):
        return f"<sync tcp Connection from: {address_to_str(self._address)}>"

    @property
    def is_closed(self):
        return self._socket is None

    def send(self, parcel):
        parcel_ref = mosaic.put(parcel.piece)
        refs_and_bundle = bundler([parcel_ref], self._seen_refs)
        self._seen_refs |= refs_and_bundle.ref_set
        data = encode_tcp_packet(refs_and_bundle.bundle)
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
        _selector.unregister(sock)
        self._socket = None

    def _process_buffer(self):
        while has_full_tcp_packet(self._buffer):
            bundle, packet_size = decode_tcp_packet(self._buffer)
            self._buffer = self._buffer[packet_size:]
            self._process_bundle(bundle)

    def _process_bundle(self, bundle):
        parcel_ref = bundle.roots[0]
        log.info("%s: Received bundle: parcel: %s", self, parcel_ref)
        ref_set = unbundler.register_bundle(bundle)
        self._seen_refs |= ref_set
        parcel = parcel_registry.invite(parcel_ref)
        sender_ref = mosaic.put(parcel.sender.piece)
        # Add route first - it may be used during parcel processing.
        log.info("%s will be routed via established connection from: %s", sender_ref, self)
        route_table.add_route(sender_ref, self._this_route)
        transport.send_parcel(parcel)


class Route:

    @classmethod
    def from_piece(cls, piece):
        return cls((piece.host, piece.port), is_local=False)

    def __init__(self, address, is_local):
        self._is_local = is_local  # True for routes produced by this process.
        self._address = address

    def __repr__(self):
        if self._is_local:
            suffix = '/local'
        else:
            suffix = ''
        return f"<sync tcp Route:{self}{suffix}>"

    def __str__(self):
        return address_to_str(self._address)

    @property
    def piece(self):
        host, port = self._address
        return htypes.tcp_transport.route(host, port)

    @property
    def available(self):
        return not self._is_local

    def send(self, parcel):
        if self._is_local:
            raise RuntimeError("Can not send parcel using TCP to myself")
        client = client_factory(self._address)
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
        if self._connection.is_closed:
            raise RuntimeError(f"Can not send {parcel} back to {self._connection}: it is already closed")
        self._connection.send(parcel)


def _selector_thread_main():
    log.info("TCP selector thread is started.")
    try:
        while not stop_signal.is_set():
            event_list = _selector.select(timeout=0.5)
            for key, mask in event_list:
                handler = key.data
                handler(key.fileobj, mask)
            for address, client in _address_to_client.items():
                if client.is_closed:
                    log.debug("Remove client %s from cache", client)
                    del _address_to_client[address]
    except Exception as x:
        log.exception("TCP selector thread is failed:")
        failed(f"TCP selector thread is failed: {x}", x)
    log.info("TCP selector thread is finished.")


def client_factory(address):
    connection = _address_to_client.get(address)
    if not connection:
        sock = socket.socket()
        sock.connect(address)
        sock.setblocking(False)
        connection = Connection(address, sock)
        _address_to_client[address] = connection
        _selector.register(sock, selectors.EVENT_READ, connection.on_read)
    return connection


def _stop():
    log.info("Stop TCP selector thread.")
    _selector_thread.join()
    log.info("TCP selector thread is stopped.")


@mark.service
def tcp_server_factory():
    def server_factory(bind_address=None):
        server = Server()
        server.start(bind_address)
        return server

    return server_factory


@route_registry.actor(htypes.tcp_transport.route)
def route_from_piece(piece):
    return Route.from_piece(piece)


_selector = selectors.DefaultSelector()
_address_to_client = {}  # (host, port) -> Connection
_selector_thread = threading.Thread(target=_selector_thread_main)

_selector_thread.start()
on_stop.append(_stop)
