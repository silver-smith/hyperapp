import logging
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import ExitStack, contextmanager

log = logging.getLogger(__name__)


class ProcessPool:

    _JobRec = namedtuple('JobRec', 'process job')

    def __init__(self, rc_job_submit_factory, process_list):
        self._rc_job_submit_factory = rc_job_submit_factory
        self._process_list = process_list
        self._free_processes = process_list[:]
        self._future_to_rec = {}
        self._job_queue = []

    @property
    def job_count(self):
        return len(self._future_to_rec) + len(self._job_queue)

    @property
    def queue_size(self):
        return len(self._job_queue)

    def submit(self, job):
        if self._free_processes:
            process = self._free_processes.pop()
            self._start_job(job, process)
        else:
            self._job_queue.append(job)

    def iter_completed(self, timeout):
        for future in as_completed(self._future_to_rec, timeout):
            rec = self._future_to_rec.pop(future)
            if self._job_queue:
                self._start_job(self._job_queue.pop(0), rec.process)
            else:
                self._free_processes.append(rec.process)
            yield (rec.job, future.result())

    def _start_job(self, job, process):
        log.info("Start at #%d: %s", self._process_list.index(process), job)
        submit = self._rc_job_submit_factory(process.peer, process.identity)
        future = submit(job)
        self._future_to_rec[future] = self._JobRec(process, job)


@contextmanager
def process_pool_running(
        endpoint_registry, rpc_endpoint, generate_rsa_identity, subprocess_rpc_server_running, rc_job_submit_factory,
        process_count, timeout):
    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    with ExitStack() as stack:

        with ThreadPoolExecutor(max_workers=process_count) as executor:

            def start_process(idx):
                return stack.enter_context(subprocess_rpc_server_running(
                    f'rc-driver-{idx:02}',
                    identity,
                    timeout_sec=timeout,
                    start_timeout_sec=timeout,
                    ))

            process_list = list(executor.map(start_process, range(process_count)))

        yield ProcessPool(rc_job_submit_factory, process_list)
