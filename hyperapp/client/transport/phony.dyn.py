import logging

from hyperapp.common.interface import phony_transport as phony_transport_types
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.phony'

class Transport(object):

    def send(self, ref):
        assert 0


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.transport_registry.register(phony_transport_types.address, self._resolve_address)

    def _resolve_address(self, address):
        return Transport()
