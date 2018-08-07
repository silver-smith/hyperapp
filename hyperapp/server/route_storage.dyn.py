# store known server's routes to database

import logging
from pony.orm import db_session, Required, select
from ..common.util import is_list_list_inst, encode_route, decode_route
from ..common.identity import PublicKey
from ..common.route_storage import RouteRepository, RouteStorage
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'server_info'


class DbRouteRepository(RouteRepository):

    def enumerate(self):
        return []

    @db_session
    def add(self, public_key, routes):
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert is_list_list_inst(routes, str), repr(routes)
        public_key_pem = public_key.to_pem()
        ## delete(rec for rec in this_module.ServerRoute if rec.public_key_pem==public_key_pem)
        for rec in select(rec for rec in this_module.ServerRoute if rec.public_key_pem==public_key_pem):
            rec.delete()
        for route in routes:
            log.info('-- storing route for %s: %r', public_key.get_short_id_hex(), encode_route(route))
            this_module.ServerRoute(
                public_key_pem=public_key_pem,
                route=encode_route(route),
                )

    @db_session
    def get(self, public_key):
        assert isinstance(public_key, PublicKey), repr(public_key)
        routes = []
        for rec in select(rec for rec in this_module.ServerRoute if rec.public_key_pem==public_key.to_pem()):
            routes.append(decode_route(rec.route))
        log.info('-- loaded routes for %s: %r', public_key.get_short_id_hex(), [encode_route(route) for route in routes])
        return routes


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        PonyOrmModule.__init__(self, MODULE_NAME)
        services.route_storage = RouteStorage(DbRouteRepository())

    def init_phase2(self, services):
        self.ServerRoute = self.make_entity(
            'ServerRoute',
            public_key_pem=Required(str),
            route=Required(str),
            )
