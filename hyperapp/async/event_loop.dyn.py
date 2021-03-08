import asyncio
import logging
import threading

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._services = services
        self._module_registry = services.module_registry
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)  # Should be set before any asyncio objects created.
        self._stop_event = asyncio.Event()
        services.event_loop = self._event_loop
        services.async_stop_event = self._stop_event
        self._thread = threading.Thread(target=self._event_loop_main)
        services.on_start.append(self.start)
        services.on_stop.append(self.stop)

    def start(self):
        self._thread.start()

    def stop(self):
        log.info("Stop async loop thread.")
        self._event_loop.call_soon_threadsafe(self._stop_event.set)
        self._thread.join()
        log.info("Async loop thread is stopped.")

    def _event_loop_main(self):
        log.info("Async thread started.")
        loop = self._event_loop
        try:
            try:
                loop.set_debug(True)
                loop.run_until_complete(self._async_main())
            finally:
                try:
                    self._cancel_all_tasks(loop)
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    # loop.run_until_complete(loop.shutdown_default_executor())  # python 3.9
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()
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
        log.info("Async main started.")
        await self._async_init_modules()
        log.info("Async modules inited.")
        await self._stop_event.wait()
        log.info("Async main finished.")

    async def _async_init_modules(self):
        for module, method in self._module_registry.enum_modules_method('async_init'):
            log.info("Async init module %r:", module.name)
            await method(self._services)
