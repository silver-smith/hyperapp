import logging

from ..common.interface import hyper_ref as href_types
from .module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'remoting'


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.transport_registry.register(href_types.service_request, self._process_request)

    def _process_request(self, request):
        assert 0, request
