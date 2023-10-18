import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager

from .services import (
    endpoint_registry,
    generate_rsa_identity,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )

log = logging.getLogger(__name__)


class ProcessPool:

    def __init__(self, process_list):
        self._process_list = process_list
        self._free_processes = process_list[:]
        self._process_available = asyncio.Condition()

    async def _allocate_process(self):
        async with self._process_available:
            while not self._free_processes:
                await self._process_available.wait()
            return self._free_processes.pop()

    async def _free_process(self, process):
        async with self._process_available:
            self._free_processes.append(process)
            self._process_available.notify()

    async def run(self, servant_fn, **kw):
        process = await self._allocate_process()
        log.info("Run at process #%d: %s(%s)", self._process_list.index(process), servant_fn, kw)
        future = process.rpc_submit(servant_fn)(**kw)
        try:
            return await asyncio.wrap_future(future)
        finally:
            await self._free_process(process)


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
