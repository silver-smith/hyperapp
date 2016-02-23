from ..common.endpoint import Endpoint


class RouteRepository(object):

    def __init__( self ):
        self.server_id2routes = {}

    def add_endpoint_routes( self, endpoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        self.server_id2routes[endpoint.public_key.get_id()] = endpoint.routes

    def get_routes( self, server_public_id ):
        return self.server_id2routes.get(server_public_id.get_id(), [])
