import asyncio
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.event_loop_ctr = self.event_loop_ctr
        services.event_loop_dtr = lambda: None

    def event_loop_ctr(self):
        return asyncio.new_event_loop()
