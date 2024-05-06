import logging
import multiprocessing
import struct
import threading
from collections import namedtuple

from hyperapp.common.htypes import bundle_t
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


# packet data size
HEADER_FORMAT = '!Q'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def encode_packet(data):
    header = struct.pack(HEADER_FORMAT, len(data))
    return header + data


class ConnectionRec:

    def __init__(self, connection, name, seen_refs, on_eof=None, on_reset=None):
        self._connection = connection
        self.name = name
        self.seen_refs = seen_refs
        self.on_eof = on_eof or self._do_nothing
        self.on_reset = on_reset or self.on_eof
        self._buffer = b''

    def _do_nothing(self):
        pass

    def close(self):
        log.info("Subprocess transport: close connection %r", self.name)
        del _server_connections[self._connection]
        self._connection.close()
        _signal_connection_in.send(None)  # Wake up server main.

    def read(self):
        self._buffer += self._connection.recv()
        if self._has_full_packet():
            return self._pop_packet()
        else:
            return None

    def _has_full_packet(self):
        if len(self._buffer) < HEADER_SIZE:
            return False
        [size] = struct.unpack(HEADER_FORMAT, self._buffer[:HEADER_SIZE])
        return len(self._buffer) >= HEADER_SIZE + size

    def _pop_packet(self):
        [size] = struct.unpack(HEADER_FORMAT, self._buffer[:HEADER_SIZE])
        packet_data = self._buffer[HEADER_SIZE : HEADER_SIZE + size]
        self._buffer = self._buffer[HEADER_SIZE + size:]
        return packet_data


class SubprocessRoute:

    def __init__(self, name, seen_refs, connection):
        self._name = name
        self._seen_refs = seen_refs
        self._connection = connection

    @property
    def piece(self):
        return None

    @property
    def available(self):
        return True

    def send(self, parcel):
        parcel_ref = mosaic.put(parcel.piece)
        refs_and_bundle = bundler([parcel_ref], self._seen_refs)
        self._seen_refs |= refs_and_bundle.ref_set
        bundle_cdr = packet_coders.encode('cdr', refs_and_bundle.bundle)
        log.debug("Subprocess transport: send bundle to %r. Bundle size: %.2f KB", self._name, len(bundle_cdr)/1024)
        self._connection.send(encode_packet(bundle_cdr))
        log.debug("Subprocess %s: parcel is sent: %s", self._name, parcel_ref)


@mark.service
def add_subprocess_server_connection():

    def _add_subprocess_server_connection(name, connection, seen_refs, on_eof=None, on_reset=None):
        rec = ConnectionRec(connection, name, seen_refs, on_eof, on_reset)
        _server_connections[connection] = rec
        _signal_connection_in.send(None)  # Wake up server main.
        return rec

    return _add_subprocess_server_connection


def _process_parcel(connection, connection_rec, parcel):
    sender_ref = mosaic.put(parcel.sender.piece)
    route = SubprocessRoute(connection_rec.name, connection_rec.seen_refs, connection)
    route_table.add_route(sender_ref, route)
    transport.send_parcel(parcel)


def _process_bundle(connection, connection_rec, data):
    log.debug("Subprocess transport: received bundle from %r. Bundle size: %.2f KB", connection_rec.name, len(data)/1024)
    parcel_bundle = packet_coders.decode('cdr', data, bundle_t)
    ref_set = unbundler.register_bundle(parcel_bundle)
    connection_rec.seen_refs |= ref_set
    parcel_piece_ref = parcel_bundle.roots[0]
    parcel = parcel_registry.invite(parcel_piece_ref)
    _process_parcel(connection, connection_rec, parcel)


def _process_ready_connection(connection):
    rec = _server_connections[connection]
    try:
        data = rec.read()
    except EOFError as x:
        log.info("Subprocess connection %s was closed by the other side: %s", rec.name, x)
        rec.on_eof()
    except (OSError, ConnectionResetError) as x:
        log.warning("Subprocess connection %s was reset by the other side: %s", rec.name, x)
        rec.on_reset()
    else:
        if data is None:
            return  # Partial packet is received.
        try:
            _process_bundle(connection, rec, data)
            return  # Keep connection.
        except Exception as x:
            my_name = f"Processing bundle from {rec.name}"
            log.exception("%s is failed:", my_name)
            failed(f"{my_name} is failed: {x}", x)
    del _server_connections[connection]
    _signal_connection_in.send(None)


def _server_thread_main():
    my_name = "Subprocess transport server thread"
    log.info("%s is started", my_name)
    try:
        while not stop_signal.is_set():
            all_connections = [_signal_connection_out, *_server_connections]
            ready_connections = multiprocessing.connection.wait(all_connections)
            for connection in ready_connections:
                if connection is not _signal_connection_out:
                    # If is just removed, both signal connection and removed connection may be ready.
                    if connection in _server_connections:
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
    _signal_connection_in.send(None)  # Wake up server main.
    _server_thread.join()
    log.info("%s is stopped", my_name)


_server_connections = {}  # connection -> ConnectionRec
_signal_connection_out, _signal_connection_in = multiprocessing.Pipe()
_server_thread = threading.Thread(target=_server_thread_main, name='SubpServer')

_server_thread.start()
on_stop.append(_stop)
