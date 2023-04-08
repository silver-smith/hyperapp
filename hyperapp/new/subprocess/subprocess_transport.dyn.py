import logging
import multiprocessing
import threading
from collections import namedtuple

from hyperapp.common.htypes.packet_coders import packet_coders

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

log = logging.getLogger(__name__)

ConnectionRec = namedtuple('ConnectionRec', 'name on_eof on_reset')


class SubprocessRoute:

    def __init__(self, name, connection):
        self._name = name
        self._connection = connection

    @property
    def piece(self):
        return None

    @property
    def available(self):
        return True

    def send(self, parcel):
        parcel_ref = mosaic.put(parcel.piece)
        parcel_bundle = bundler([parcel_ref]).bundle
        bundle_cdr = packet_coders.encode('cdr', parcel_bundle)
        self._connection.send(bundle_cdr)
        log.debug("Subprocess %s: parcel is sent: %s", self._name, parcel_ref)


@mark.service
def add_server_connection(name, connection, on_eof, on_reset):
    _server_connections[connection] = ConnectionRec(name, on_eof, on_reset)


def _process_parcel(connection, connection_rec, parcel):
    sender_ref = mosaic.put(parcel.sender.piece)
    route = SubprocessRoute(connection_rec.name, connection)
    route_table.add_route(sender_ref, route)
    transport.send_parcel(parcel)


def _process_bundle(connection, connection_rec, data):
    parcel_bundle = packet_coders.decode('cdr', data, bundle_t)
    unbundler.register_bundle(parcel_bundle)
    parcel_piece_ref = parcel_bundle.roots[0]
    parcel = parcel_registry.invite(parcel_piece_ref)
    _process_parcel(connection, connection_rec, parcel)


def _process_ready_connection(connection):
    rec = _server_connections[connection]
    try:
        data = connection.recv()
    except EOFError as x:
        log.info("Subprocess connection %s was closed by the other side: %s", rec.name, x)
        rec.on_eof()
    except ConnectionResetError as x:
        log.exception("Subprocess connection %s was reset by the other side: %s", rec.name, x)
        rec.on_reset()
    else:
        try:
            _process_bundle(connection, rec, data)
            return  # Keep connection.
        except Exception as x:
            my_name = f"Processing bundle from {rec.name}"
            log.exception("%s is failed:", my_name)
            failed(f"{my_name} is failed: {x}", x)
    del _server_connections[connection]


def _server_thread_main():
    my_name = "Subprocess transport server thread"
    log.info("%s is started", my_name)
    try:
        while not stop_signal.is_set():
            all_connections = [_signal_connection_out, *_server_connections]
            ready_connections = multiprocessing.connection.wait(all_connections)
            for connection in ready_connections:
                if connection is not self._signal_connection_out:
                    _process_ready_connection(connection)
                else:
                    connection.recv()  # Clear signal connection
    except Exception as x:
        log.exception("%s is failed:", my_name)
        failed(f"{my_name} is failed: {x}", x)
    log.info("%s is finished", my_name)


def _stop():
    my_name = "Subprocess transport server thread"
    log.info("Stop %s", my_name)
    _server_thread.join()
    log.info("%s is stopped", my_name)


_server_connections = {}  # connection -> ConnectionRec
_signal_connection_out, _signal_connection_in = multiprocessing.Pipe()
_server_thread = threading.Thread(target=_server_thread_main)

_server_thread.start()
on_stop.append(_stop)
