import logging
import selectors
import socket

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class Server:

    def __init__(self, selector):
        self._selector = selector
        self._sock = socket.socket()
        self._actual_address = None

    def start(self, bind_address):
        self._sock.bind(bind_address)
        self._sock.listen(100)
        self._sock.setblocking(False)
        self._selector.register(self._sock, selectors.EVENT_READ, self._on_accept)
        self._actual_address = self._sock.getsockname()
        host, port = self._actual_address
        log.info("Listening on %s:%d", host, port)

    @property
    def route(self):
        return Route(self._actual_address)

    def _on_accept(self, listen_sock, mask):
        sock, address = listen_sock.accept()
        log.info("Accepted connection from %s:%d", *address)
        raise NotImplementedError('todo')


class Route:

    @classmethod
    def from_piece(cls, piece):
        return cls((piece.route.host, piece.route.port))

    def __init__(self, address):
        self._address = address

    def __repr__(self):
        host, port = self._address
        return f'tcp_route({host}:{port})'

    @property
    def piece(self):
        host, port = self._address
        return htypes.tcp_transport.route(host, port)

    def send(self, parcel):
        raise NotImplementedError('todo')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._selector = selectors.DefaultSelector()
        services.route_registry.register_actor(htypes.tcp_transport.route, Route.from_piece)
        services.tcp_server = self.server_factory

    def server_factory(self, bind_address):
        server = Server(self._selector)
        server.start(bind_address)
        return server
