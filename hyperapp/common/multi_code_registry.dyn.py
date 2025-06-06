import logging

from .services import (
    deduce_t,
    )

log = logging.getLogger(__name__)


class MultiCodeRegistry:

    def __init__(self, service_name, config):
        self._service_name = service_name
        self._config = config  # t -> item list

    def ui_type_items(self, ui_t):
        ui_t_t = deduce_t(ui_t)
        return self._config.get(ui_t_t, [])
