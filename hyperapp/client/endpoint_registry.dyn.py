from ..common.interface import hyper_ref as href_types
from .module import ClientModule


MODULE_NAME = 'endpoint_registry'


class EndpointRegistry(object):

    def __init__(self, ref_registry):
        self._ref_registry = ref_registry
        self._endpoint_set = set()

    def register_endpoint(self, endpoint):
        endpoint_ref = self._ref_registry.register_object(href_types.endpoint, endpoint)
        self._endpoint_set.add(endpoint_ref)
        return endpoint_ref

    def get_endpoint_ref_list(self):
        return list(self._endpoint_set)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.endpoint_registry = EndpointRegistry(services.ref_registry)
