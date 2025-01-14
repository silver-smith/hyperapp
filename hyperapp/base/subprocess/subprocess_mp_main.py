import logging
import logging.handlers
import traceback
import threading
from contextlib import contextmanager

from hyperapp.boot.htypes import bundle_t
from hyperapp.boot import cdr_coders  # self-registering
from hyperapp.boot.htypes.packet_coders import packet_coders
from hyperapp.boot.services import HYPERAPP_DIR, Services

log = logging.getLogger(__name__)


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


def subprocess_main_safe(connection, main_fn_bundle_cdr):
    log.info("Subprocess: Init services.")
    services = Services()
    services.init_services()

    pyobj_creg = services.pyobj_creg
    unbundler = services.unbundler

    log.info("Subprocess: Unpack main function. Bundle size: %.2f KB", len(main_fn_bundle_cdr)/1024)

    bundle = packet_coders.decode('cdr', main_fn_bundle_cdr, bundle_t)
    received_refs = unbundler.register_bundle(bundle)
    main_fn_ref = bundle.roots[0]
    main_fn = pyobj_creg.invite(main_fn_ref)

    log.info("Subprocess: Run main function %s: %s", main_fn_ref, main_fn)
    try:
        main_fn(connection, received_refs)
    finally:
        log.info("Subprocess: Stopping services.")
        services.stop()
        log.info("Subprocess: Services are stopped. Exiting.")
