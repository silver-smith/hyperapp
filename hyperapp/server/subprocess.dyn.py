import logging
import logging.handlers
import multiprocessing
import multiprocessing.connection
import sys
import threading
from collections import namedtuple
from pathlib import Path

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .subprocess_connection import ConnectionEvent, SubprocessRoute

log = logging.getLogger(__name__)


def log_traceback(traceback_entries):
    for entry in traceback_entries:
        for line in entry.splitlines():
            log.error("%s", line.rstrip())


class Process:

    def __init__(self, name, this_module, mp_process, connection):
        self.name = name
        self._this_module = this_module
        self._mp_process = mp_process
        self._connection = connection
        self._stopped_event = threading.Event()
        self._is_stopped = False
        self._exception = None
        self._traceback_entries = None

    def __enter__(self):
        log.info("Start subprocess %r", self.name)
        self._this_module.subprocess_started(self, self._connection)
        self._mp_process.start()

    def __exit__(self, exc, value, tb):
        log.info("Exit subprocess %r", self.name)
        self._connection.send((ConnectionEvent.STOP.value, None))
        self._stopped_event.wait()  # Process should send 'stopped' signal.
        self._mp_process.join()
        if self._exception is not None:
            log.error("Exception in subprocess %r: %s", self.name, self._exception)
            log_traceback(self._traceback_entries)
            raise self._exception

    def signal_is_stopped_now(self, exception=None, traceback_entries=None):
        self._exception = exception
        self._traceback_entries = traceback_entries
        self._stopped_event.set()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._ref_collector_factory = services.ref_collector_factory
        self._unbundler = services.unbundler
        self._route_a9n_registry = services.route_a9n_registry
        self._parcel_registry = services.parcel_registry
        self._on_failure = services.failed
        self._transport = services.transport
        self._work_dir = services.work_dir / 'subprocess'
        self._mp_context = multiprocessing.get_context('forkserver')
        self._stop_flag = False
        self._signal_connection_out, self._signal_connection_in = self._mp_context.Pipe()
        self._connection_to_process = {self._signal_connection_out: None}
        self._thread = threading.Thread(target=self._recv_thread_main)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)
        services.subprocess = self.subprocess

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_flag = True
        self._signal_connection_in.send(None)
        self._thread.join()

    def _recv_thread_main(self):
        log.info("Subprocess recv thread is started.")
        try:
            while not self._stop_flag or len(self._connection_to_process) > 1:
                self._receive_and_process_bundle()
        except Exception as x:
            log.exception("Subprocess recv thread is failed:")
            self._on_failure("Subprocess recv thread is failed: %r" % x)
        log.info("Subprocess recv thread is finished.")

    def _receive_and_process_bundle(self):
        ready_connections = multiprocessing.connection.wait(self._connection_to_process.keys())
        for connection in ready_connections:
            process = self._connection_to_process[connection]
            if process:
                self._recv_bundle(process, connection)

    def _recv_bundle(self, process, connection):
        event, payload = connection.recv()
        log.debug("Subprocess recv thread: received %s from %s: %s", event, process.name, payload)
        if event != ConnectionEvent.PARCEL.value:
            self._process_stop_event(process, connection, event, payload)
            return
        try:
            parcel_bundle = packet_coders.decode('cdr', payload, bundle_t)
            self._unbundler.register_bundle(parcel_bundle)
            parcel_piece_ref = parcel_bundle.roots[0]
            parcel = self._parcel_registry.invite(parcel_piece_ref)
            self._process_parcel(connection, parcel)
        except Exception as x:
            log.exception("Error processing parcel from subprocess %r", process.name)
            self._on_failure(f"Error processing parcel from subprocess {process.name!r}: {x}")

    def _process_parcel(self, connection, parcel):
        sender_ref = self._mosaic.put(parcel.sender.piece)
        child_route = SubprocessRoute(self._mosaic, self._ref_collector_factory, connection)
        self._route_a9n_registry.associate(sender_ref, child_route)
        self._transport.send_parcel(parcel)

    def _process_stop_event(self, process, connection, event, payload):
        del self._connection_to_process[connection]
        if event == ConnectionEvent.EXCEPTION.value:
            exception, traceback_entries = payload
        else:
            exception = traceback_entries = None
        process.signal_is_stopped_now(exception, traceback_entries)

    def subprocess(self, process_name, type_module_list, code_module_list, config=None):
        # todo: add subprocess_mp_main.py to module data.
        source_dir = Path.cwd() / 'hyperapp' / 'server'
        subprocess_mp_main = source_dir / 'subprocess_mp_main.py'
        sys.path.append(str(source_dir))
        module = __import__('subprocess_mp_main', level=0)
        main_fn = module.subprocess_main

        parent_connection, child_connection = self._mp_context.Pipe()
        args = [process_name, child_connection, type_module_list, code_module_list, config]
        mp_process = self._mp_context.Process(target=main_fn, args=args)
        return Process(process_name, self, mp_process, parent_connection)

    def subprocess_started(self, process, connection):
        self._connection_to_process[connection] = process
        self._signal_connection_in.send(None)
