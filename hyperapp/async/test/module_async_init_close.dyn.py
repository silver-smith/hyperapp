import asyncio
import logging
import threading

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._stop_event = services.async_stop_event
        self._test_stop_event = threading.Event()
        services.test_init_event = threading.Event()
        services.test_stop_event = self._test_stop_event

    async def async_init(self, services):
        log.info("Test async init close: started.")
        services.test_init_event.set()

    async def async_stop(self):
        log.info("Test async init close: got stop event.")
        self._test_stop_event.set()
