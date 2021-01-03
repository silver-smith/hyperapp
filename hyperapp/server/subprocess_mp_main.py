import logging
import logging.handlers
import traceback
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


def subprocess_main(process_name, logger_queue, connection, type_module_list, code_module_list, config):
    try:
        memory_handler = init_logging(process_name, logger_queue)
        subprocess_main_safe(connection, type_module_list, code_module_list, config)
        connection.send((ConnectionEvent.STOP.value, None))
    except Exception as x:
        log.error("Exception in subprocess: %s", x)
        traceback_entries = traceback.format_tb(x.__traceback__)
        log_traceback(traceback_entries)
        # Traceback is not pickleable, convert it to string list.
        connection.send((ConnectionEvent.EXCEPTION.value, (x, traceback_entries)))
    memory_handler.flush()


def init_logging(process_name, logger_queue):

    def filter(record):
        if not hasattr(record, 'context'):
            record.context = process_name
        return True

    queue_handler = logging.handlers.QueueHandler(logger_queue)
    queue_handler.addFilter(filter)
    memory_handler = logging.handlers.MemoryHandler(1000, target=queue_handler)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(memory_handler)
    return memory_handler


def subprocess_main_safe(connection, type_module_list, code_module_list, config):
    services = Services()
    services.master_process_connection = connection
    services.init_services()
    services.init_modules(type_module_list, code_module_list, config)
    services.start()
    log.info("Running, waiting for stop signal.")
    _unused = connection.recv()  # Wait for stop signal.
    log.info("Received stop signal; stopping.")
    services.stop()
    log.info("Stopped.")
