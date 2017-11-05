import logging
from ..common.interface import hyper_ref as href_types
from .registry import Registry
from .module import Module

log = logging.getLogger(__name__)


class ServiceRegistry(Registry):

    def resolve(self, service):
        tclass = href_types.service.get_object_class(service)
        rec = self._resolve(tclass.id)
        log.info('producing service %r using %s(%s, %s)', tclass.id, rec.factory, rec.args, rec.kw)
        return rec.factory(service, *rec.args, **rec.kw)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.service_registry = ServiceRegistry()
