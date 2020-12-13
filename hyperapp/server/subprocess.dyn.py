import logging
import logging.handlers
import multiprocessing
import sys
import traceback
from pathlib import Path

from hyperapp.common.services import Services
from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def subprocess_main(process_name, logger_queue, connection, type_module_list, code_module_list):
    try:
        init_logging(process_name, logger_queue)
        subprocess_main_safe(connection, type_module_list, code_module_list)
        connection.send(None)  # Send 'process finished' signal.
    except Exception as x:
        log.error("Exception in subprocess: %s, %r", x, x.__traceback__)
        # Traceback is not pickleable, convert it to string list.
        connection.send((x, traceback.format_tb(x.__traceback__)))


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


def subprocess_main_safe(connection, type_module_list, code_module_list):
    # raise RuntimeError('test error')
    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    log.info("Running, waiting for stop signal.")
    unused = connection.recv()  # Wait for stop signal.
    services.stop()


class Process:

    def __init__(self, name, mp_process, logger_queue, connection):
        self._name = name
        self._mp_process = mp_process
        self._logger_queue = logger_queue
        self._connection = connection
        self._log_queue_listener = None

    def __enter__(self):
        root_logger = logging.getLogger()
        self._log_queue_listener = logging.handlers.QueueListener(self._logger_queue, root_logger)
        self._log_queue_listener.start()
        self._mp_process.start()

    def __exit__(self, exc, value, tb):
        self._connection.send(None)  # Send stop signal.
        result = self._connection.recv()  # Wait for 'process finished' signal.
        self._mp_process.join()
        self._log_queue_listener.enqueue_sentinel()
        self._log_queue_listener.stop()
        if result:
            exception, traceback = result
            log.error("Exception in subprocess %s: %s\n%s", self._name, exception, ''.join(traceback))
            raise exception


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        self._work_dir = services.work_dir / 'subprocess'
        self._mp_context = multiprocessing.get_context('spawn')
        services.subprocess = self.subprocess

    def subprocess(self, process_name, type_module_list, code_module_list):
        self._work_dir.mkdir(parents=True, exist_ok=True)
        subprocess_mp_main = self._work_dir / 'subprocess_mp_main.py'
        subprocess_mp_main.write_text(__module_source__)
        sys.path.append(str(self._work_dir))
        module = __import__('subprocess_mp_main', level=0)
        main_fn = module.subprocess_main

        logger_queue = self._mp_context.Queue()
        parent_connection, child_connection = self._mp_context.Pipe()
        args = [process_name, logger_queue, child_connection, type_module_list, code_module_list]
        mp_process = self._mp_context.Process(target=main_fn, args=args)
        return Process(process_name, mp_process, logger_queue, parent_connection)
