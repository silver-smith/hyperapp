import asyncio
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._state_storage = services.application_state_storage
        self._async_stop_event = services.async_stop_event
        self._root_view = services.root_view
        self._default_state_builder = services.default_state_builder
        self._view_registry = services.view_registry
        services.open_application = self.open_application

    async def open_application(self):
        log.info("Load application state.")
        state = self._state_storage.load_state()
        if state is None:
            state = self._default_state_builder()
        self._root_view.init(await self._view_registry.animate(state))
        # Construct windows only after all modules are (async) inited - registered all their actors.
        asyncio.get_running_loop().create_task(self._open(state))

    async def _open(self, state):
        try:
            await self._root_view.open(state)
        except:
            self._async_stop_event.set()
            raise

    async def async_stop(self):
        if self._root_view:  # Services init failed before layout constructed?
            log.info("Save application state.")
            state = self._root_view.state
            if not state.window_list:
                # Init still failed.
                log.warning("Not saving application state with no windows")
                return
            self._state_storage.save_state(state)
