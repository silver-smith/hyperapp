from hyperapp.common.module import Module


class LocalRoute:

    def __init__(self, endpoint):
        self._endpoint = endpoint

    def send(self, parcel):
        self._endpoint.process(parcel)


class EndpointRegistry:

    def __init__(self, route_a9n_registry):
        self._route_a9n_registry = route_a9n_registry

    def register(self, peer_ref, endpoint):
        self._route_a9n_registry.associate(peer_ref, LocalRoute(endpoint))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.endpoint_registry = EndpointRegistry(services.route_a9n_registry)

