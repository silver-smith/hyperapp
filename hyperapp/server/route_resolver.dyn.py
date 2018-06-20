import logging
import abc

from ..common.ref import ref_repr
from .module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'server_info'


class RouteSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def resolve(self, endpoint_ref):
        pass


class RouteRegistry(RouteSource):

    def __init__(self):
        self._endpoint_ref_to_transport_ref_set = {}

    def add_route(self, endpoint_ref, transport_ref):
        log.info('route registry: adding route %s -> %s', ref_repr(endpoint_ref), ref_repr(transport_ref))
        self._endpoint_ref_to_transport_ref_set.setdefault(endpoint_ref, set()).add(transport_ref)

    def resolve(self, endpoint_ref):
        return self._endpoint_ref_to_transport_ref_set.get(endpoint_ref, set())

        
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
        return transport_ref_set


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.route_resolver = RouteResolver()
