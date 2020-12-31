import logging
import logging.handlers
import multiprocessing
import sys
from collections import namedtuple
from pathlib import Path

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .subprocess_connection import ConnectionEvent

log = logging.getLogger(__name__)


def log_traceback(traceback_entries):
    for entry in traceback_entries:
        for line in entry.splitlines():
            log.error("%s", line.rstrip())


class Process:

    def __init__(self, name, mp_process, logger_queue, connection, unbundler, parcel_registry):
        self._name = name
        self._mp_process = mp_process
        self._logger_queue = logger_queue
        self._connection = connection
        self._unbundler = unbundler
        self._parcel_registry = parcel_registry
        self._log_queue_listener = None
        self._is_stopped = False

    def __enter__(self):
        root_logger = logging.getLogger()
        self._log_queue_listener = logging.handlers.QueueListener(self._logger_queue, root_logger)
        self._log_queue_listener.start()
        self._mp_process.start()

    def __exit__(self, exc, value, tb):
        self._connection.send((ConnectionEvent.STOP.value, ()))
        event, payload = self._connection.recv()  # Wait for stop or exception signal.
        self._mp_process.join()
        self._log_queue_listener.enqueue_sentinel()
        self._log_queue_listener.stop()
        if event == ConnectionEvent.EXCEPTION.value:
            exception, traceback_entries = payload
            log.error("Exception in subprocess %s: %s", self._name, exception)
            log_traceback(traceback_entries)
            raise exception

    def recv_parcel(self):
        event, payload = self._connection.recv()
        if event != ConnectionEvent.PARCEL.value:
            self._process_stop_event()
        parcel_bundle = packet_coders.decode('cdr', payload, bundle_t)
        self._unbundler.register_bundle(parcel_bundle)
        parcel_piece_ref = parcel_bundle.roots[0]
        return self._parcel_registry.invite(parcel_piece_ref)

    def _process_stop_event(self):
        assert 0, 'todo'


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._unbundler = services.unbundler
        self._parcel_registry = services.parcel_registry
        self._work_dir = services.work_dir / 'subprocess'
        self._mp_context = multiprocessing.get_context('forkserver')
        services.subprocess = self.subprocess

    def subprocess(self, process_name, type_module_list, code_module_list, config=None):
        # todo: add subprocess_mp_main.py to module data.
        source_dir = Path.cwd() / 'hyperapp' / 'server'
        subprocess_mp_main = source_dir / 'subprocess_mp_main.py'
        sys.path.append(str(source_dir))
        module = __import__('subprocess_mp_main', level=0)
        main_fn = module.subprocess_main

        logger_queue = self._mp_context.Queue()
        parent_connection, child_connection = self._mp_context.Pipe()
        args = [process_name, logger_queue, child_connection, type_module_list, code_module_list, config]
        mp_process = self._mp_context.Process(target=main_fn, args=args)
        return Process(process_name, mp_process, logger_queue, parent_connection, self._unbundler, self._parcel_registry)
