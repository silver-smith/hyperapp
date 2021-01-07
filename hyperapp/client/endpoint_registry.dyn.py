from datetime import datetime

from dateutil.tz import tzlocal

from hyperapp.common.ref import LOCAL_TRANSPORT_REF
from hyperapp.client.module import ClientModule
from .route_resolver import RouteSource
from .htypes.hyper_ref import route_rec


class EndpointRegistry(object):

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._endpoint_set = set()

    def register_endpoint(self, endpoint):
        endpoint_ref = self._mosaic.put(endpoint)
        self.register_endpoint_ref(endpoint_ref)
        return endpoint_ref

    def register_endpoint_ref(self, endpoint_ref):
        self._endpoint_set.add(endpoint_ref)

    def is_registered(self, endpoint_ref):
        return endpoint_ref in self._endpoint_set


class LocalRouteSource(RouteSource):

    def __init__(self, endpoint_registry):
        self._endpoint_registry = endpoint_registry

    def resolve(self, endpoint_ref):
        if self._endpoint_registry.is_registered(endpoint_ref):
            return [route_rec(LOCAL_TRANSPORT_REF, datetime.now(tzlocal()))]
        else:
            return []


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.endpoint_registry = endpoint_registry = EndpointRegistry(services.mosaic)
        services.route_resolver.add_source(LocalRouteSource(endpoint_registry))
