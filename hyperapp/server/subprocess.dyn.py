import logging
import multiprocessing
import sys
import traceback
from pathlib import Path

from hyperapp.common.services import Services
from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def subprocess_main(connection, type_module_list, code_module_list):
    try:
        subprocess_main_safe(connection, type_module_list, code_module_list)
        connection.send(None)
    except Exception as x:
        log.error("Exception in subprocess: %s, %r", x, x.__traceback__)
        # Traceback is not pickleable, convert it to string list.
        connection.send((x, traceback.format_tb(x.__traceback__)))


def subprocess_main_safe(connection, type_module_list, code_module_list):
    # raise RuntimeError('test error')
    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    unused = connection.recv()  # Wait for stop signal.
    services.stop()


class Process:

    def __init__(self, mp_process, connection):
        self._mp_process = mp_process
        self._connection = connection

    def __enter__(self):
        self._mp_process.start()

    def __exit__(self, exc, value, tb):
        self._connection.send(None)  # Send stop signal.
        result = self._connection.recv()
        self._mp_process.join()
        if result:
            exception, traceback = result
            log.error("Exception in subprocess: %s\n%s", exception, ''.join(traceback))
            raise exception


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        self._work_dir = services.work_dir / 'subprocess'
        self._mp_context = multiprocessing.get_context('forkserver')
        services.subprocess = self.subprocess

    def subprocess(self, type_module_list, code_module_list):
        self._work_dir.mkdir(parents=True, exist_ok=True)
        subprocess_mp_main = self._work_dir / 'subprocess_mp_main.py'
        subprocess_mp_main.write_text(__module_source__)
        sys.path.append(str(self._work_dir))
        module = __import__('subprocess_mp_main', level=0)
        main_fn = module.subprocess_main

        parent_connection, child_connection = self._mp_context.Pipe()
        mp_process = self._mp_context.Process(target=main_fn, args=[child_connection, type_module_list, code_module_list])
        return Process(mp_process, parent_connection)
