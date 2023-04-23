import logging
import logging.handlers
import traceback
import threading
from contextlib import contextmanager
from enum import Enum

from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


# Note: copy shared with subprocess_connection.dyn.py
class ConnectionEvent(Enum):
    STOP = 1
    EXCEPTION = 2
    PARCEL = 3


def log_traceback(traceback_entries):
    for entry in traceback_entries:
        for line in entry.splitlines():
            log.error("%s", line.rstrip())


def subprocess_main(process_name, connection, module_dir_list, code_module_list, config):
    with logging_inited(process_name):
        try:
            subprocess_main_safe(connection, module_dir_list, code_module_list, config)
            connection.send((ConnectionEvent.STOP.value, None))
        except Exception as x:
            log.error("Exception in subprocess: %r", x)
            traceback_entries = traceback.format_tb(x.__traceback__)
            log_traceback(traceback_entries)
            # Traceback is not pickleable, convert it to string list.
            connection.send((ConnectionEvent.EXCEPTION.value, (x, traceback_entries)))


@contextmanager
def logging_inited(process_name):
    format = '%(asctime)s.%(msecs)03d %(name)-46s %(lineno)4d %(threadName)10s %(levelname)-8s  %(message)s'
    datefmt = '%H:%M:%S'
    handler = logging.FileHandler(f'/tmp/{process_name}.log', mode='w')
    handler.setFormatter(logging.Formatter(format, datefmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    try:
        yield
    finally:
        handler.close()


def init_meta_registry_association(resource_registry, python_object_creg):
    resource = resource_registry['common.meta_registry_association', 'meta_registry_association.module']
    module = python_object_creg.animate(resource)
    module.init()


additional_code_module_list = [
    'resource.resource_module',
    'resource.register_associations',
    'sync.subprocess_child',
    ]


def subprocess_main_safe(connection, module_dir_list, code_module_list, config):
    services = Services(module_dir_list)
    services.master_process_connection = connection
    services.subprocess_stop_event = threading.Event()
    services.init_services()
    services.init_modules(code_module_list + additional_code_module_list, config)
    init_meta_registry_association(services.resource_registry, services.python_object_creg)
    services.register_associations(services.resource_registry)
    services.start_modules()
    log.info("Running, waiting for stop signal.")
    services.subprocess_stop_event.wait()
    log.info("Got stop signal, stopping subprocess services.")
    services.stop_signal.set()
    services.stop()
    log.info("Subprocess services are stopped.")
