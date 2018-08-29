import logging
import abc

from .ref import ref_repr, ref_list_repr
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'route_resolver'


class RouteSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def resolve(self, endpoint_ref):
        pass


class RouteRegistry(RouteSource):

    def __init__(self):
        self._registry = {}

    def resolve(self, endpoint_ref):
        return self._registry.get(endpoint_ref, set())

    def register(self, endpoint_ref, transport_ref):
        log.info('Route registry: adding route %s -> %s', ref_repr(endpoint_ref), ref_repr(transport_ref))
        self._registry.setdefault(endpoint_ref, set()).add(transport_ref)

    def register_route(self, route):
        self.register(route.endpoint_ref, route.transport_ref)

        
class RouteResolver(object):

    def __init__(self):
        self._source_list = []

    def add_source(self, source):
        assert isinstance(source, RouteSource), repr(source)
        self._source_list.append(source)

    def remove_source(self, source):
        self._source_list.remove(source)

    def resolve(self, service_ref):
        transport_ref_set = set()
        for source in self._source_list:
            transport_ref_set |= source.resolve(service_ref)
        log.info('Route resolver: %s resolved to %s', ref_repr(service_ref), ref_list_repr(transport_ref_set))
        return transport_ref_set


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.route_resolver = route_resolver = RouteResolver()
        services.route_registry = route_registry = RouteRegistry()
        route_resolver.add_source(route_registry)
