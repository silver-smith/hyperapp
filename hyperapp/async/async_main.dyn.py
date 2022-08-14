import asyncio
import logging
import threading
from functools import partial

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class EventLoopHolder:

    def __init__(self):
        self._loop = None
        self._lock = threading.Lock()

    def set_loop(self, loop):
        with self._lock:
            assert not self._loop
            self._loop = loop

    def clear_loop(self):
        with self._lock:
            assert self._loop
            self._loop = None

    def create_task_if_started(self, coro):
        with self._lock:
            if not self._loop:
                return
            self._loop.call_soon_threadsafe(partial(self._run_coro, self._loop, coro))

    def _run_coro(self, loop, coro):
        loop.create_task(coro)


class AsyncStopEvent:

    def __init__(self):
        self._event = None

    # Async event can be created only in event loop thread.
    def init(self, event):
        self._event = event

    async def wait(self):
        await self._event.wait()

    def set(self):
        self._event.set()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._services = services
        self._module_registry = services.module_registry
        self._event_loop_ctr = services.event_loop_ctr
        self._event_loop_dtr = services.event_loop_dtr
        self._sync_stop_signal = services.stop_signal
        self._event_loop = None
        self._async_stop_event = AsyncStopEvent()
        self._event_loop_holder = EventLoopHolder()
        self._thread = threading.Thread(target=self._event_loop_main)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)
        services.async_stop_event = self._async_stop_event
        services.event_loop_holder = self._event_loop_holder

    def start(self):
        self._thread.start()

    def stop(self):
        log.info("Stop async loop thread.")
        self._event_loop.call_soon_threadsafe(self._async_stop_event.set)
        self._event_loop_holder.clear_loop()
        self._thread.join()
        log.info("Async loop thread is stopped.")

    # Copy of 'run' and '_cancel_all_tasks' functions from asyncio/runners.py
    def _event_loop_main(self):
        log.info("Async thread started.")
        loop = self._event_loop_ctr()
        loop.set_debug(True)
        asyncio.set_event_loop(loop)  # Should be set before any asyncio objects created.
        self._event_loop_holder.set_loop(loop)
        self._event_loop = loop
        self._async_stop_event.init(asyncio.Event())
        try:
            try:
                loop.run_until_complete(self._async_main())
            finally:
                try:
                    self._cancel_all_tasks(loop)
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    # loop.run_until_complete(loop.shutdown_default_executor())  # python 3.9
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()
                    self._event_loop_dtr()
                    log.info("Async thread finished.")
        except Exception as x:
            log.exception("Async thread failed.")

    def _cancel_all_tasks(self, loop):
        to_cancel = asyncio.all_tasks(loop)
        if not to_cancel:
            return

        for task in to_cancel:
            task.cancel()

        loop.run_until_complete(
            asyncio.gather(*to_cancel, loop=loop, return_exceptions=True))

        for task in to_cancel:
            if task.cancelled():
                continue
            if task.exception() is not None:
                loop.call_exception_handler({
                    'message': 'unhandled exception during asyncio.run() shutdown',
                    'exception': task.exception(),
                    'task': task,
                })

    async def _async_main(self):
        try:
            log.info("Async main started.")
            await self._async_init_modules()
            log.info("Async modules inited.")
            await self._async_stop_event.wait()
        finally:
            try:
                await self._async_stop_modules()
            finally:
                self._sync_stop_signal.set()
                log.info("Async main finished.")

    async def _async_init_modules(self):
        for module_name, method in self._module_registry.enum_method('async_init'):
            log.info("Async init module %r:", module_name)
            await method(self._services)

    async def _async_stop_modules(self):
        for module_name, method in self._module_registry.enum_method('async_stop'):
            log.info("Async stop module %r:", module_name)
            await method()
