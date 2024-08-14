import logging
import multiprocessing
import struct
import threading
from collections import namedtuple

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    failed,
    mosaic,
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

    def __init__(self, subprocess_transport, connection, name, seen_refs, on_eof=None, on_reset=None):
        self._subprocess_transport = subprocess_transport
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
        self._connection.close()
        self._subprocess_transport.server_connection_closed(self._connection)

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

    def __init__(self, bundler, name, seen_refs, connection):
        self._bundler = bundler
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
        refs_and_bundle = self._bundler([parcel_ref], self._seen_refs)
        self._seen_refs |= refs_and_bundle.ref_set
        bundle_cdr = packet_coders.encode('cdr', refs_and_bundle.bundle)
        log.debug("Subprocess transport: send bundle to %r. Bundle size: %.2f KB", self._name, len(bundle_cdr)/1024)
        try:
            self._connection.send(encode_packet(bundle_cdr))
        except OSError as x:
            if str(x) == 'handle is closed':
                raise RuntimeError(f"Error sending message to subprocess {self._name!r}: subprocess is gone") from x
            else:
                raise
        log.debug("Subprocess %s: parcel is sent: %s", self._name, parcel_ref)


class SubprocessTransport:

    def __init__(self, bundler, parcel_registry, transport, route_table):
        self._bundler = bundler
        self._parcel_registry = parcel_registry
        self._transport = transport
        self._route_table = route_table
        self._server_connections = {}  # connection -> ConnectionRec
        self._is_stopping = False
        out_c, in_c = multiprocessing.Pipe()
        self._signal_connection_in = in_c
        self._signal_connection_out = out_c
        self._server_thread = threading.Thread(target=self._server_thread_main, name='SubpServer')
        self._server_thread.start()

    def add_server_connection(self, name, connection, seen_refs, on_eof=None, on_reset=None):
        rec = ConnectionRec(self, connection, name, seen_refs, on_eof, on_reset)
        self._server_connections[connection] = rec
        self._signal_connection_in.send(None)  # Wake up server main.
        return rec

    def server_connection_closed(self, connection):
        del self._server_connections[connection]
        self._signal_connection_in.send(None)  # Wake up server main.

    def stop(self):
        my_name = "Subprocess transport server thread"
        log.info("Stop %s", my_name)
        self._is_stopping = True
        self._signal_connection_in.send(None)  # Wake up server main.
        self._server_thread.join()
        log.info("%s is stopped", my_name)

    def _server_thread_main(self):
        my_name = "Subprocess transport server thread"
        log.info("%s is started", my_name)
        try:
            while not self._is_stopping:
                all_connections = [self._signal_connection_out, *self._server_connections]
                ready_connections = multiprocessing.connection.wait(all_connections)
                for connection in ready_connections:
                    if connection is not self._signal_connection_out:
                        # If is just removed, both signal connection and removed connection may be ready.
                        if connection in self._server_connections:
                            self._process_ready_connection(connection)
                    else:
                        connection.recv()  # Clear signal connection
        except Exception as x:
            log.exception("%s is failed:", my_name)
            failed(f"{my_name} is failed: {x}", x)
        log.info("%s is finished", my_name)

    def _process_ready_connection(self, connection):
        rec = self._server_connections[connection]
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
                self._process_bundle(connection, rec, data)
                return  # Keep connection.
            except Exception as x:
                my_name = f"Processing bundle from {rec.name}"
                log.exception("%s is failed:", my_name)
                failed(f"{my_name} is failed: {x}", x)
        del self._server_connections[connection]
        self._signal_connection_in.send(None)

    def _process_bundle(self, connection, connection_rec, data):
        log.debug("Subprocess transport: received bundle from %r. Bundle size: %.2f KB", connection_rec.name, len(data)/1024)
        parcel_bundle = packet_coders.decode('cdr', data, bundle_t)
        ref_set = unbundler.register_bundle(parcel_bundle)
        connection_rec.seen_refs |= ref_set
        parcel_piece_ref = parcel_bundle.roots[0]
        parcel = self._parcel_registry.invite(parcel_piece_ref)
        self._process_parcel(connection, connection_rec, parcel)

    def _process_parcel(self, connection, connection_rec, parcel):
        sender_ref = mosaic.put(parcel.sender.piece)
        route = SubprocessRoute(self._bundler, connection_rec.name, connection_rec.seen_refs, connection)
        self._route_table.add_route(sender_ref, route)
        self._transport.send_parcel(parcel)


def subprocess_transport(bundler, parcel_registry, transport, route_table):
    transport = SubprocessTransport(bundler, parcel_registry, transport, route_table)
    yield transport
    transport.stop()
