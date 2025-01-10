import logging
import multiprocessing
import sys
from contextlib import contextmanager
from pathlib import Path

from hyperapp.boot.htypes.packet_coders import packet_coders

from .services import (
    mosaic,
    )

log = logging.getLogger(__name__)


_mp_context = multiprocessing.get_context('spawn')


class _Subprocess:

    def __init__(self, connection, sent_refs):
        self.connection = connection
        self.sent_refs = sent_refs


def subprocess_running(bundler):

    @contextmanager
    def _subprocess_running(name, main_fn_ref):
        # TODO: Move subprocess_mp_main.py to data resource.
        source_dir = Path.cwd() / 'hyperapp/subprocess'
        subprocess_mp_main = source_dir / 'subprocess_mp_main.py'
        sys.path.append(str(source_dir))
        module = __import__('subprocess_mp_main', level=0)
        subprocess_main = module.subprocess_main

        refs_and_bundle = bundler([main_fn_ref])
        bundle_cdr = packet_coders.encode('cdr', refs_and_bundle.bundle)
        log.info("Subprocess %s: Packed main function. Bundle size: %.2f KB", name, len(bundle_cdr)/1024)

        parent_connection, child_connection = _mp_context.Pipe()
        subprocess_args = [name, child_connection, bundle_cdr]
        process = _mp_context.Process(target=subprocess_main, args=subprocess_args)
        process.start()

        try:
            yield _Subprocess(parent_connection, refs_and_bundle.ref_set)
        finally:
            parent_connection.close()  # Signal child to stop.
            log.info("Joining process %s...", name)
            process.join()
            log.info("Joining process %s: done", name)

    return _subprocess_running
