import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._stop_event = services.async_stop_event
        self._async_web = services.async_web
        self._layout_manager = services.layout_manager
        self._default_state_builder = services.default_state_builder
        self._state_storage = services.application_state_storage

    async def async_init(self, services):
        await self._load_state()

    async def async_stop(self):
        self._save_state()

    async def _load_state(self):
        log.info("Load application state.")
        app_state = self._state_storage.load_state()
        if app_state:
            root_layout_state = await self._async_web.summon(app_state.root_layout_ref)
        else:
            root_layout_state = self._default_state_builder()
        await self._layout_manager.create_layout_views(root_layout_state)

    def _save_state(self):
        log.info("Save application state.")
        state = self._get_current_state()
        self._state_storage.save_state(state)

    def _get_current_state(self):
        root_layout = self._layout_manager.root_layout.piece
        root_layout_ref = self._mosaic.put(root_layout)
        return self._state_storage.state_t(
            root_layout_ref=root_layout_ref,
            )
