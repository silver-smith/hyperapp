import logging
import multiprocessing
import threading

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .subprocess_connection import ConnectionEvent, SubprocessRoute

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._master_process_connection = services.master_process_connection
        self._subprocess_stop_event = services.subprocess_stop_event
        self._on_failure = services.failed
        self._unbundler = services.unbundler
        self._transport = services.transport
        self._parcel_registry = services.parcel_registry

        master_peer_ref_cdr_list = config.get('master_peer_ref_cdr_list', [])
        master_peer_ref_list = [
            packet_coders.decode('cdr', ref_cdr, ref_t)
            for ref_cdr in master_peer_ref_cdr_list
            ]

        master_process_route = SubprocessRoute(services.mosaic, services.ref_collector_factory, services.master_process_connection)
        for peer_ref in master_peer_ref_list:
            services.route_table.add_route(peer_ref, master_process_route)

        self._stop_flag = False
        self._signal_connection_out, self._signal_connection_in = multiprocessing.Pipe()
        self._thread = threading.Thread(target=self._recv_thread_main)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)

    def start(self):
        log.info("Start subprocess child recv thread.")
        self._thread.start()

    def stop(self):
        log.info("Stop subprocess child recv thread.")
        self._stop_flag = True
        self._signal_connection_in.send(None)
        self._thread.join()
        log.info("Subprocess child recv thread is stopped.")

    def _recv_thread_main(self):
        log.info("Subprocess recv thread is started.")
        try:
            while not self._stop_flag:
                self._receive_and_process_bundle()
        except Exception as x:
            log.exception("Subprocess recv thread is failed:")
            self._on_failure("Subprocess recv thread is failed: %r" % x)
        log.info("Subprocess recv thread is finished.")

    def _receive_and_process_bundle(self):
        ready_connections = multiprocessing.connection.wait([self._signal_connection_out, self._master_process_connection])
        for connection in ready_connections:
            if connection is not self._signal_connection_out:
                self._recv_bundle()

    def _recv_bundle(self):
        event, payload = self._master_process_connection.recv()
        log.info("Subprocess recv thread: received %s: %s", event, payload)
        if event != ConnectionEvent.PARCEL.value:
            self._process_stop_event()
            return
        try:
            parcel_bundle = packet_coders.decode('cdr', payload, bundle_t)
            self._unbundler.register_bundle(parcel_bundle)
            parcel_piece_ref = parcel_bundle.roots[0]
            parcel = self._parcel_registry.invite(parcel_piece_ref)
            self._process_parcel(parcel)
        except Exception as x:
            log.exception("Error processing parcel from master process")

    def _process_parcel(self, parcel):
        self._transport.send_parcel(parcel)

    def _process_stop_event(self):
        self._subprocess_stop_event.set()
