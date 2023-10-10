import logging
from collections import namedtuple
from concurrent.futures import as_completed
from contextlib import ExitStack, contextmanager

from .services import (
    endpoint_registry,
    generate_rsa_identity,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )

log = logging.getLogger(__name__)



class ProcessPool:

    _TaskRec = namedtuple('TaskRec', 'process task')

    def __init__(self, process_list):
        self._process_list = process_list
        self._free_processes = process_list[:]
        self._future_to_rec = {}
        self._task_queue = []

    @property
    def task_count(self):
        return len(self._future_to_rec) + len(self._task_queue)

    def _start_task(self, task, process):
        log.info("Start at #%d: %s", self._process_list.index(process), task)
        future = task.start(process)
        self._future_to_rec[future] = self._TaskRec(process, task)

    def submit(self, task):
        if self._free_processes:
            process = self._free_processes.pop()
            self._start_task(task, process)
        else:
            self._task_queue.append(task)

    def next_completed(self, timeout):
        future = next(as_completed(self._future_to_rec, timeout))
        rec = self._future_to_rec.pop(future)
        if self._task_queue:
            self._start_task(self._task_queue.pop(0), rec.process)
        else:
            self._free_processes.append(rec.process)
        return (rec.task, future)


@contextmanager
def process_pool_running(process_count, rpc_timeout):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with ExitStack() as stack:
        process_list = [
            stack.enter_context(
                subprocess_rpc_server_running(
                    f'rc-driver-{idx:02}',
                    rpc_endpoint,
                    identity,
                    timeout_sec=rpc_timeout,
                    ))
            for idx in range(process_count)
            ]
        yield ProcessPool(process_list)
