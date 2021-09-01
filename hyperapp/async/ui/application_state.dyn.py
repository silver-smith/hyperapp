import asyncio
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._state_storage = services.application_state_storage
        self._root_view = None

    async def async_init(self, services):
        log.info("Load application state.")
        state = self._state_storage.load_state()
        if state is None:
            state = services.default_state_builder()
        self._root_view = await services.view_registry.animate(state)
        services.root_view = self._root_view
        # Construct windows only after all modules are (async) inited - registered all their actors.
        asyncio.get_event_loop().create_task(self._open(state))

    async def _open(self, state):
        await self._root_view.open(state)

    async def async_stop(self):
        if self._root_view:  # Services init failed before layout constructed?
            log.info("Save application state.")
            state = self._root_view.state
            self._state_storage.save_state(state)
