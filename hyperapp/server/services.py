import os.path
import logging
from ..common.htypes import TypeRegistryRegistry, tModule, iface_registry, builtin_type_registry
from ..common.route_storage import RouteStorage
from ..common.type_repository import TypeRepository
from .module import Module
from .module_manager import ModuleManager
from . import route_storage
from .remoting import Remoting
from . import tcp_transport
from . import encrypted_transport
from .resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
DYN_MODULE_EXT = '.dyn.py'


class Services(object):

    def __init__( self ):
        self.server_dir = os.path.abspath(os.path.dirname(__file__))
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../common/interface'))
        self.iface_registry = iface_registry
        self.dynamic_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamic_modules'))
        self.type_registry_registry = TypeRegistryRegistry(dict(builtins=builtin_type_registry()))
        self.type_repository = TypeRepository(self.interface_dir, self.iface_registry, self.type_registry_registry)
        self.module_manager = ModuleManager(self, self.type_registry_registry)
        self.modules = self.module_manager.modules
        self.resources_loader = ResourcesLoader(dict(interface=self.server_dir,
                                                     client_module=self.dynamic_module_dir))
        self.route_storage_module = route_storage.ThisModule()
        self.module_manager.register_meta_hook()
        self._load_type_modules()
        self._load_server_modules()
        Module.init_phases()
        self.route_storage = RouteStorage(route_storage.DbRouteRepository(self.route_storage_module))
        self.remoting = Remoting(self.iface_registry)
        self._register_transports()

    def _register_transports( self ):
        for module in [tcp_transport, encrypted_transport]:
            module.register_transports(self.remoting.transport_registry, self)

    def _load_type_modules( self ):
        for module_name in [
                'code_repository',
                'admin',
                'article',
                'blog',
                'fs',
                'module_list',
                'test_list',
                'text_object_types',
                ]:
            fpath = os.path.join(self.interface_dir, module_name + TYPE_MODULE_EXT)
            self.type_repository.load_module(module_name, fpath)

    def _load_server_modules( self ):
        for module_name in [
                'server_management',
                'client_code_repository',
                'admin',
                'module_list',
                'fs',
                'article',
                'blog',
                'simple_text_object',
                'sample_list',
                ]:
            fpath = os.path.join(self.server_dir, module_name + DYN_MODULE_EXT)
            with open(fpath) as f:
                source = f.read()
            package = 'hyperapp.server'
            module = tModule(id=module_name, package=package, deps=[], satisfies=[], source=source, fpath=fpath)
            self.module_manager.add_code_module(module)
