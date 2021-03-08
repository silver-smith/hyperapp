import asyncio
import logging
import threading

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._stop_event = services.async_stop_event
        services.test_init_event = threading.Event()
        services.test_stop_event = threading.Event()

    async def async_init(self, services):
        log.info("Test async init close: started.")
        services.test_init_event.set()
        await asyncio.wait_for(self._stop_event.wait(), timeout=10)
        log.info("Test async init close: got stop event.")
        services.test_stop_event.set()
