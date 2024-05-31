import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    endpoint_registry,
    generate_rsa_identity,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )

log = logging.getLogger(__name__)


class ProcessWaitError(RuntimeError):
    pass


class ProcessPool:

    def __init__(self, process_list):
        self._process_list = process_list
        self._free_processes = process_list[:]
        self._process_available = asyncio.Condition()

    async def _allocate_process(self):
        async with self._process_available:
            while not self._free_processes:
                try:
                    await self._process_available.wait()
                except asyncio.CancelledError:
                    raise ProcessWaitError("Cancelled while waiting for a process be available")
            return self._free_processes.pop()

    async def _free_process(self, process):
        async with self._process_available:
            self._free_processes.append(process)
            self._process_available.notify_all()

    async def run(self, servant_fn, **kw):
        process = await self._allocate_process()
        process_idx = self._process_list.index(process)
        log.info("Process #%d: run: %s(%s)", process_idx, servant_fn, kw)
        future = process.rpc_submit(servant_fn)(**kw)
        try:
            result = await asyncio.wrap_future(future)
            log.info("Process #%d: result: %s", process_idx, result)
            return result
        except HException as x:
            if isinstance(x, htypes.rpc.server_error):
                log.error("Process #%d: server error: %s", process_idx, x.message)
                for entry in x.traceback:
                    for line in entry.splitlines():
                        log.error("%s", line)
            raise
        finally:
            await self._free_process(process)

    async def check_for_deadlock(self):
        try:
            async with asyncio.timeout(6) as timeout:
                async with self._process_available:
                    log.debug("Deadlock check: setup")
                    while True:
                        await self._process_available.wait()
                        when = asyncio.get_running_loop().time() + 10
                        log.debug("Deadlock check: reschedule to %s", when)
                        timeout.reschedule(when)
        except asyncio.CancelledError:
            pass
        except TimeoutError:
            raise


@contextmanager
def process_pool_running(process_count, rpc_timeout):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    with ExitStack() as stack:

        with ThreadPoolExecutor(max_workers=process_count) as executor:

            def start_process(idx):
                return stack.enter_context(subprocess_rpc_server_running(
                    f'rc-driver-{idx:02}',
                    rpc_endpoint,
                    identity,
                    timeout_sec=rpc_timeout,
                    ))

            process_list = list(executor.map(start_process, range(process_count)))

        yield ProcessPool(process_list)
