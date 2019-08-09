import logging
import abc

from hyperapp.client.module import ClientModule

log = logging.getLogger(__name__)


class AsyncRouteSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def resolve(self, service_ref):
        pass


class AsyncRouteResolver(object):

    def __init__(self, route_resolver):
        self._route_resolver = route_resolver
        self._async_source_list = []

    def add_async_source(self, source):
        assert isinstance(source, AsyncRouteSource), repr(source)
        self._async_source_list.append(source)

    async def resolve(self, endpoint_ref):
        rec_set = self._route_resolver.resolve(endpoint_ref)
        # Although we may have some transport refs now, they all may be unaccessible.
        # But we do not want to request routes again for every rpc call.
        if rec_set:
            return rec_set
        for source in self._async_source_list:
            rec_set |= await source.resolve(endpoint_ref)
        return rec_set


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.async_route_resolver = AsyncRouteResolver(services.route_resolver)
