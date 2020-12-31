import logging
import logging.handlers
import multiprocessing
import sys
import traceback
from collections import namedtuple
from pathlib import Path

from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.services import Services
from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def log_traceback(traceback_entries):
    for entry in traceback_entries:
        for line in entry.splitlines():
            log.error("%s", line.rstrip())


def subprocess_main(process_name, logger_queue, connection, type_module_list, code_module_list, config, master_peer_ref_cdr_list):
    try:
        init_logging(process_name, logger_queue)
        subprocess_main_safe(connection, type_module_list, code_module_list, config, master_peer_ref_cdr_list)
        connection.send((ConnectionEvent.STOP.value, ()))
    except Exception as x:
        log.error("Exception in subprocess: %s", x)
        traceback_entries = traceback.format_tb(x.__traceback__)
        log_traceback(traceback_entries)
        # Traceback is not pickleable, convert it to string list.
        connection.send((ConnectionEvent.EXCEPTION.value, (x, traceback_entries)))


def init_logging(process_name, logger_queue):

    def filter(record):
        if not hasattr(record, 'context'):
            record.context = process_name
        return True

    handler = logging.handlers.QueueHandler(logger_queue)
    handler.addFilter(filter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)


def subprocess_main_safe(connection, type_module_list, code_module_list, config, master_peer_ref_cdr_list):
    master_peer_ref_list = [
        packet_coders.decode('cdr', ref_cdr, ref_t)
        for ref_cdr in master_peer_ref_cdr_list
        ]

    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list, config)
    init_subprocess_modules(connection, services)
    services.start()
    log.info("Running, waiting for stop signal.")
    unused = connection.recv()  # Wait for stop signal.
    services.stop()


def init_subprocess_modules(connection, services):
    services.master_process_route = SubprocessRoute(services.ref_registry, services.ref_collector_factory, connection)


class Process:

    def __init__(self, name, mp_process, logger_queue, connection):
        self._name = name
        self._mp_process = mp_process
        self._logger_queue = logger_queue
        self._connection = connection
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
        parcel_piece = packet_coders.decode('cdr', payload, ref_t)

    def _process_stop_event(self):
        assert 0, 'todo'


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._work_dir = services.work_dir / 'subprocess'
        self._mp_context = multiprocessing.get_context('forkserver')
        services.subprocess = self.subprocess

    def subprocess(self, process_name, type_module_list, code_module_list, config=None, master_peer_ref_list=None):
        self._work_dir.mkdir(parents=True, exist_ok=True)
        subprocess_mp_main = self._work_dir / 'subprocess_mp_main.py'
        subprocess_mp_main.write_text(__module_source__)
        sys.path.append(str(self._work_dir))
        module = __import__('subprocess_mp_main', level=0)
        main_fn = module.subprocess_main

        logger_queue = self._mp_context.Queue()
        parent_connection, child_connection = self._mp_context.Pipe()
        master_peer_ref_cdr_list = [packet_coders.encode('cdr', ref) for ref in master_peer_ref_list or []]
        args = [process_name, logger_queue, child_connection, type_module_list, code_module_list, config, master_peer_ref_cdr_list]
        mp_process = self._mp_context.Process(target=main_fn, args=args)
        return Process(process_name, mp_process, logger_queue, parent_connection)
