import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        self._stop_event = services.async_stop_event
        self._async_web = services.async_web
        self._default_state_builder = services.default_state_builder
        self._state_storage = services.application_state_storage
        self._view_registry = services.view_registry
        self._root_view = None

    async def async_init(self, services):
        await self._load_state()

    async def async_stop(self):
        self._save_state()

    async def _load_state(self):
        log.info("Load application state.")
        state = self._state_storage.load_state()
        if state is None:
            state = self._default_state_builder()
        self._root_view = await self._view_registry.animate(state)

    def _save_state(self):
        log.info("Save application state.")
        if self._root_view:  # Services init failed before layout constructed?
            state = self._root_view.state
            self._state_storage.save_state(state)
