import logging
import select
import selectors
import socket
import threading
from collections import namedtuple
from functools import partial

from . import htypes
from .services import (
    mosaic,
    unbundler,
    )
from .code.mark import mark
from .code.tcp_utils import address_to_str, has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


_Services = namedtuple('_Services', [
    'bundler',
    'parcel_registry',
    'transport',
    'route_table',
    'address_to_tcp_client',
    'tcp_selector',
    ])


class Server:

    def __init__(self, svc, tcp_client_factory):
        self._svc = svc
        self._tcp_client_factory = tcp_client_factory
        self._listen_socket = socket.socket()
        self._actual_address = None
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __repr__(self):
        return f"<sync tcp Server:{address_to_str(self._actual_address)}>"

    def start(self, bind_address=None):
        self._listen_socket.bind(bind_address or ('localhost', 0))
        self._listen_socket.listen(100)
        self._listen_socket.setblocking(False)
        self._svc.tcp_selector.register(self._listen_socket, selectors.EVENT_READ, self._on_accept)
        self._actual_address = self._listen_socket.getsockname()
        log.info("%s: Listening.", self)

    @property
    def route(self):
        return Route(self._tcp_client_factory, self._actual_address, is_local=True)

    def _on_accept(self, listen_sock, mask):
        sock, address = listen_sock.accept()
        log.info("%s: Accepted connection from %s", self, address_to_str(address))
        sock.setblocking(False)
        connection = Connection(self._svc, address, sock)
        self._svc.tcp_selector.register(sock, selectors.EVENT_READ, connection.on_read)


class Connection:

    def __init__(self, svc, address, sock):
        self._svc = svc
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
        refs_and_bundle = self._svc.bundler([parcel_ref], self._seen_refs)
        self._seen_refs |= refs_and_bundle.ref_set
        data = encode_tcp_packet(refs_and_bundle.bundle)
        ofs = 0
        while ofs < len(data):
            sent_size = self._socket_send(data[ofs:])
            log.debug("%s: Sent %d bytes", self, sent_size)
            if sent_size == 0:
                raise RuntimeError(f"{self}: remote end closed connection")
            ofs += sent_size
        log.info("%s: Parcel is sent: %s", self, parcel_ref)

    def _socket_send(self, data):
        while True:
            try:
                return self._socket.send(data)
            except OSError as x:
                if x.errno != socket.errno.EAGAIN:
                    raise
            rd, wr, er = select.select([], [self._socket], [])
            assert wr

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
        self._svc.tcp_selector.unregister(sock)
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
        parcel = self._svc.parcel_registry.invite(parcel_ref)
        sender_ref = mosaic.put(parcel.sender.piece)
        # Add route first - it may be used during parcel processing.
        log.info("%s will be routed via established connection from: %s", sender_ref, self)
        self._svc.route_table.add_route(sender_ref, self._this_route)
        self._svc.transport.send_parcel(parcel)


class Route:

    @classmethod
    @mark.actor.route_registry(htypes.tcp_transport.route)
    def from_piece(cls, piece, tcp_client_factory):
        return cls(tcp_client_factory, (piece.host, piece.port), is_local=False)

    def __init__(self, tcp_client_factory, address, is_local):
        self._tcp_client_factory = tcp_client_factory
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
        client = self._tcp_client_factory(self._address)
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


@mark.service
def _address_to_tcp_client():
    return {}  # (host, port) -> Connection


@mark.service
def _tcp_selector(system_failed, _address_to_tcp_client):
    tcp_stop_signal = threading.Event()
    selector = selectors.DefaultSelector()

    def main():
        log.info("TCP selector thread is started.")
        try:
            while not tcp_stop_signal.is_set():
                event_list = selector.select(timeout=0.5)
                for key, mask in event_list:
                    handler = key.data
                    handler(key.fileobj, mask)
                for address, client in list(_address_to_tcp_client.items()):
                    if client.is_closed:
                        log.debug("Remove client %s from cache", client)
                        del _address_to_tcp_client[address]
        except Exception as x:
            log.exception("TCP selector thread is failed:")
            system_failed(f"TCP selector thread is failed: {x}", x)
        log.info("TCP selector thread is finished.")

    thread = threading.Thread(target=main, name="TCP-selector")
    thread.start()

    yield selector

    log.info("Stop TCP selector thread.")
    tcp_stop_signal.set()
    thread.join()
    log.info("TCP selector thread is stopped.")


@mark.service
def _tcp_services(
        bundler,
        parcel_registry,
        transport,
        route_table,
        _address_to_tcp_client,
        _tcp_selector,
        ):
    return _Services(
        bundler=bundler,
        parcel_registry=parcel_registry,
        transport=transport,
        route_table=route_table,
        address_to_tcp_client=_address_to_tcp_client,
        tcp_selector=_tcp_selector,
        )


@mark.service
def tcp_client_factory(_tcp_services, address):
    svc = _tcp_services
    connection = svc.address_to_tcp_client.get(address)
    if not connection:
        sock = socket.socket()
        sock.connect(address)
        sock.setblocking(False)
        connection = Connection(svc, address, sock)
        svc.address_to_tcp_client[address] = connection
        svc.tcp_selector.register(sock, selectors.EVENT_READ, connection.on_read)
    return connection


@mark.service
def tcp_server_factory(_tcp_services, tcp_client_factory, bind_address=None):
    server = Server(_tcp_services, tcp_client_factory)
    server.start(bind_address)
    return server
