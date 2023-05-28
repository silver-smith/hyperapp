import logging
import logging.handlers
import traceback
import threading
from contextlib import contextmanager

from hyperapp.common.htypes import bundle_t
from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.services import HYPERAPP_DIR, Services

log = logging.getLogger(__name__)


module_dir_list = [
    HYPERAPP_DIR / 'common',
    HYPERAPP_DIR / 'resource',
    HYPERAPP_DIR / 'sync',
    HYPERAPP_DIR / 'rpc',
    HYPERAPP_DIR / 'transport',
    HYPERAPP_DIR / 'subprocess',
    HYPERAPP_DIR / 'guesser',
    HYPERAPP_DIR / 'ui_types',
    ]

code_module_list = [
    'resource.registry',
    'resource.resource_module',
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.call',
    'resource.python_module',
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


def subprocess_main(process_name, connection, main_fn_bundle_cdr):
    with logging_inited(process_name):
        try:
            subprocess_main_safe(connection, main_fn_bundle_cdr)
        except Exception as x:
            log.exception("Subprocess: Failed with exception: %r", x)
        connection.close()


additional_code_module_list = [
    'resource.resource_module',
    ]


def subprocess_main_safe(connection, main_fn_bundle_cdr):
    log.info("Subprocess: Init services.")
    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list + additional_code_module_list)
    # TODO: Remove loading resources after all code registries (or, at least python_object_creg) moved to dynamic/associations.
    services.association_reg.register_association_list(services.resource_registry.associations)
    services.start_modules()
    log.info("Subprocess: Unpack main function. Bundle size: %.2f KB", len(main_fn_bundle_cdr)/1024)

    python_object_creg = services.python_object_creg
    unbundler = services.unbundler
    stop_signal = services.stop_signal

    bundle = packet_coders.decode('cdr', main_fn_bundle_cdr, bundle_t)
    unbundler.register_bundle(bundle)
    main_fn_ref = bundle.roots[0]
    main_fn = python_object_creg.invite(main_fn_ref)

    log.info("Subprocess: Run main function %s: %s", main_fn_ref, main_fn)
    main_fn(connection)

    log.info("Subprocess: Stopping services.")
    stop_signal.set()
    services.stop()
    log.info("Subprocess: Services are stopped. Exiting.")
