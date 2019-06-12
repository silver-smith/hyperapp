import abc
from collections import namedtuple
import logging
from typing import Sequence, Set

from hyperapp.common.ref import ref_repr, ref_list_repr
from hyperapp.common.module import Module
from .htypes.hyper_ref import route_rec

log = logging.getLogger(__name__)


MODULE_NAME = 'route_resolver'


class RouteSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def resolve(self, endpoint_ref) -> Sequence[route_rec]:
        pass


class RouteRegistry(RouteSource):

    def __init__(self):
        self._registry = {}  # endpoint_ref -> route_rec list

    def resolve(self, endpoint_ref) -> Sequence[route_rec]:
        return self._registry.get(endpoint_ref, [])

    def register(self, route):
        log.info('Route registry: adding route %s -> %s @ %s',
                 ref_repr(route.endpoint_ref), ref_repr(route.transport_ref), route.available_at)
        rec_list = self._registry.setdefault(route.endpoint_ref, [])
        rec_list.append(route_rec(route.transport_ref, route.available_at))

        
class RouteResolver(object):

    def __init__(self):
        self._source_list = []

    def add_source(self, source):
        assert isinstance(source, RouteSource), repr(source)
        self._source_list.append(source)

    def remove_source(self, source):
        self._source_list.remove(source)

    def resolve(self, service_ref) -> Set[route_rec]:
        rec_set = set()
        for source in self._source_list:
            rec_set |= set(source.resolve(service_ref))
        log.info('Route resolver: %s resolved to %d recs', ref_repr(service_ref), len(rec_set))
        return rec_set


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.route_resolver = route_resolver = RouteResolver()
        services.route_registry = route_registry = RouteRegistry()
        route_resolver.add_source(route_registry)
