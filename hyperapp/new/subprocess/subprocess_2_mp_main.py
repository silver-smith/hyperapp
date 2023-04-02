import logging
import logging.handlers
import traceback
import threading
from contextlib import contextmanager

from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.services import HYPERAPP_DIR, Services

log = logging.getLogger(__name__)


module_dir_list = [
    HYPERAPP_DIR / 'common',
    HYPERAPP_DIR / 'resource',
    ]

code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'resource.resource_type',
    'resource.registry',
    'resource.resource_module',
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.call',
    'resource.list_service',
    'resource.live_list_service',
    'resource.tree_service',
    'resource.piece_ref',
    'resource.typed_piece',
    'resource.selector',
    'resource.rpc_command',
    # 'resource.rpc_callback',
    # 'resource.map_service',
    'resource.python_module',
    'resource.raw',
    ]


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


def subprocess_main(process_name, connection):
    with logging_inited(process_name):
        try:
            subprocess_main_safe(connection)
        except Exception as x:
            log.error("Exception in subprocess: %r", x)
        connection.close()


def subprocess_main_safe(connection):
    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list)
    services.start_modules()
    log.info("Running subprocess.")

    log.info("Stopping subprocess services.")
    services.stop()
    log.info("Subprocess services are stopped.")
