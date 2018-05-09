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
        services.transport_registry.register(href_types.service_request, self._process_request, services.types, service_registry)

    def _process_request(self, request, types, service_registry):
        iface = types.resolve(request.iface_full_type_name)
        params_t = iface[request.command_id].request
        params = request.params.decode(params_t)
        servant = service_registry.resolve(request.service_id)
        request_util = None
        method = getattr(servant, 'remote_' + request.command_id, None)
        assert method, '%r does not implement method remote_%s' % (servant, request.command_id)
        method(request_util, **params._asdict())
        assert 0, servant
