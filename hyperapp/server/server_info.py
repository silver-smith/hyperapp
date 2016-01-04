# store known server's endpoints to database

from pony.orm import db_session, Required
from ..common.util import encode_route, decode_route
from ..common.identity import PublicKey
from ..common.endpoint import Endpoint
from .ponyorm_module import PonyOrmModule


MODULE_NAME = 'server_info'


def store_server_routes( endpoint ):
    module.store_server_routes(endpoint)

def load_server_routes( public_key ):
    return module.load_server_routes(public_key)


class ServerInfoModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2( self ):
        self.ServerRoute = self.make_entity(
            'ServerRoute',
            server_public_key_pem=Required(unicode),
            route=Required(unicode),
            )

    @db_session
    def store_server_routes( self, endoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        for route in endpoint.routes:
            self.ServerRoute(
                public_key_pem=endpoint.public_key.to_pem(),
                route=encode_route(route),
                )

    @db_session
    def load_server_routes( self, public_key ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        public_key_pem = public_key.to_pem()
        routes = []
        for rec in select(rec for rec in self.ServerRoute if rec.public_key_pem==public_key_pem):
            routes.append(decode_route(rec.route))
        return Endpoint(public_key, routes)


module = ServerInfoModule()
