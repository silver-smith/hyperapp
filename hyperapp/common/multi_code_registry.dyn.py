import logging

log = logging.getLogger(__name__)


class MultiCodeRegistry:

    def __init__(self, service_name, config):
        self._service_name = service_name
        self._config = config  # t -> item list

    def get_items(self, t):
        return self._config.get(t, [])
