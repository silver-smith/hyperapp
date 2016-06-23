from ..route_storage import RouteRepository


class PhonyRouteRepository(RouteRepository):

    def enumerate( self ):
        return []

    def add( self, public_key, routes ):
        pass
