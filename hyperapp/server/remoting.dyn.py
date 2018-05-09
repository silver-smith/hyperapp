import logging

from ..common.interface import hyper_ref as href_types
from .registry import Registry
from .module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'remoting'


class ServiceRegistry(Registry):

    def resolve(self, service_id):
        rec = self._resolve(service_id)
        log.info('producing service for %r using %s(%s, %s)', service_id, rec.factory, rec.args, rec.kw)
        return rec.factory(*rec.args, **rec.kw)


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.service_registry = service_registry = ServiceRegistry()
        services.transport_registry.register(href_types.service_request, self._process_request, service_registry)

    def _process_request(self, request, service_registry):
        servant = service_registry.resolve(request.service_id)
        assert 0, servant
