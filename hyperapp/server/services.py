import os.path
import sys
import logging
import importlib
from ..common.htypes import IfaceRegistry, TypeRegistryRegistry, tModule, make_request_types, builtin_type_registry
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
        self.request_types = make_request_types()
        self.iface_registry = IfaceRegistry()
        self.dynamic_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamic_modules'))
        self.type_registry_registry = TypeRegistryRegistry(dict(builtins=builtin_type_registry()))
        self.type_repository = TypeRepository(self.interface_dir, self.request_types, self.iface_registry, self.type_registry_registry)
        self.module_manager = ModuleManager(self, self.type_registry_registry)
        self.modules = self.module_manager.modules
        self.resources_loader = ResourcesLoader(dict(interface=self.server_dir,
                                                     client_module=self.dynamic_module_dir))
        self.route_storage_module = route_storage.ThisModule()
        self.module_manager.register_meta_hook()
        self._load_core_type_module()
        self.type_repository.set_core_types(self.core_types)
        self._load_type_modules()
        self._load_server_modules()
        Module.init_phases()
        self.route_storage = RouteStorage(route_storage.DbRouteRepository(self.route_storage_module))
        self.remoting = Remoting(self.iface_registry)
        self._register_transports()

    def _register_transports( self ):
        for module in [tcp_transport, encrypted_transport]:
            module.register_transports(self.remoting.transport_registry, self)

    def _load_core_type_module( self ):
        self._load_type_module('core')
        core_types = sys.modules.get('hyperapp.common.interface.core')
        if core_types:
            self.core_types = importlib.reload(core_types)
        else:
            self.core_types = importlib.import_module('hyperapp.common.interface.core')
        assert self.core_types.object is self.type_registry_registry.resolve_type_registry('core').resolve('object')

    def _load_type_modules( self ):
        for module_name in [
                'server_management',
                'code_repository',
                'splitter',
                'form',
                'admin',
                'article',
                'blog',
                'fs',
                'module_list',
                'test_list',
                'text_object_types',
                ]:
            self._load_type_module(module_name)

    def _load_type_module( self, module_name ):
        fpath = os.path.join(self.interface_dir, module_name + TYPE_MODULE_EXT)
        self.type_repository.load_module(module_name, fpath)

    def _load_server_modules( self ):
        for module_name in [
                'server_management',
                'client_code_repository',
                'form',
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
