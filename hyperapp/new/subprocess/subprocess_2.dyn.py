import logging
import multiprocessing
import sys
from contextlib import contextmanager
from pathlib import Path

from .services import (
    bundler,
    mark,
    mosaic,
    )

log = logging.getLogger(__name__)


_mp_context = multiprocessing.get_context('spawn')


class _Subprocess:

    def __init__(self):
        pass


@mark.service
def subprocess_running_2():

    @contextmanager
    def subprocess_ctx_mgr(name):
        # TODO: Move subprocess_mp_main.py to data resource.
        source_dir = Path.cwd() / 'hyperapp/new/subprocess'
        subprocess_mp_main = source_dir / 'subprocess_mp_main.py'
        sys.path.append(str(source_dir))
        module = __import__('subprocess_2_mp_main', level=0)
        subprocess_main = module.subprocess_main

        parent_connection, child_connection = _mp_context.Pipe()
        subprocess_args = [name, child_connection]
        process = _mp_context.Process(target=subprocess_main, args=subprocess_args)
        process.start()

        yield _Subprocess()

        parent_connection.close()  # Signal child to stop.
        process.join()

    return subprocess_ctx_mgr
