import logging

from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'route_resolver'


class RouteRegistry(object):

    def __init__(self):
        self._registry = {}  # service ref -> transport ref set

    def register(self, service_ref, transport_ref):
        self._registry.setdefault(service_ref, set()).add(transport_ref)

    async def resolve(self, service_ref):
        return self._registry.get(service_ref) or set()


class RouteResolver(object):

    def __init__(self):
        self._source_list = []

    def add_source(self, source):
        self._source_list.append(source)

    async def resolve(self, service_ref):
        transport_ref_set = set()
        for source in self._source_list:
            transport_ref_set |= await source.resolve(service_ref)
        return transport_ref_set


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.route_registry = route_registry = RouteRegistry()
        services.route_resolver = route_resolver = RouteResolver()
        route_resolver.add_source(route_registry)
