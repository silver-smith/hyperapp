from ..common.htypes import iface_registry
from ..common.route_storage import RouteStorage
from .module import Module
from . import route_storage
from .remoting import Remoting
from . import tcp_transport
from . import encrypted_transport


class Services(object):

    def __init__( self ):
        self.iface_registry = iface_registry
        self.route_storage_module = route_storage.ThisModule()
        self._register_modules()
        Module.init_phases()
        self.route_storage = RouteStorage(route_storage.DbRouteRepository(self.route_storage_module))
        self.remoting = Remoting(self.iface_registry)
        self._register_transports()

    def _register_modules( self ):
        for module in [
            ]:
            module.ThisModule(self)  # will auto-register itself
        
    def _register_transports( self ):
        for module in [tcp_transport, encrypted_transport]:
            module.register_transports(self.remoting.transport_registry, self)
