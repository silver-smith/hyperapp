import asyncio
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.event_loop = event_loop = asyncio.new_event_loop()
        event_loop.set_debug(True)
        asyncio.set_event_loop(event_loop)  # Should be set before any asyncio objects created.
