from collections import namedtuple

from hyperapp.common.module import Module


Request = namedtuple('Request', 'receiver_identity sender ref_list')


class LocalRoute:

    def __init__(self, unbundler, identity, endpoint):
        self._unbundler = unbundler
        self._identity = identity
        self._endpoint = endpoint

    def send(self, parcel):
        bundle = self._identity.decrypt_parcel(parcel)
        self._unbundler.register_bundle(bundle)
        request = Request(self._identity, parcel.sender, bundle.roots)
        self._endpoint.process(request)


class EndpointRegistry:

    def __init__(self, mosaic, unbundler, route_a9n_registry):
        self._mosaic = mosaic
        self._unbundler = unbundler
        self._route_a9n_registry = route_a9n_registry

    def register(self, identity, endpoint):
        peer_ref = self._mosaic.distil(identity.peer.piece)
        route = LocalRoute(self._unbundler, identity, endpoint)
        self._route_a9n_registry.associate(peer_ref, route)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.endpoint_registry = EndpointRegistry(services.mosaic, services.unbundler, services.route_a9n_registry)

