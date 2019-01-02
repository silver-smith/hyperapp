import logging

from hyperapp.common.ref import ref_repr
from hyperapp.common.registry import Registry
from hyperapp.client.module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'service_registry'


class ClientServiceRegistry(Registry):

    def __init__(self, endpoint_registry):
        super().__init__()
        self._endpoint_registry = endpoint_registry

    def id_to_str(self, id):
        return ref_repr(id)

    def register(self, service_ref, factory, *args, **kw):
        super().register(service_ref, factory, *args, **kw)
        self._endpoint_registry.register_endpoint_ref(service_ref)

    def resolve(self, service_ref):
        rec = self._resolve(service_ref)
        log.info('ServiceRegistry: producing service for %r using %s(%s, %s)', ref_repr(service_ref), rec.factory, rec.args, rec.kw)
        return rec.factory(*rec.args, **rec.kw)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.service_registry = ClientServiceRegistry(services.endpoint_registry)
