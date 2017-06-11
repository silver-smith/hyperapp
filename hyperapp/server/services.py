import os.path
import logging
from ..common.route_storage import RouteStorage
from ..common.module_manager import ModuleManager
from ..common.services import ServicesBase
from .module import Module
from . import route_storage
from .remoting import Remoting
from . import tcp_transport
from . import encrypted_transport
from .resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


DYN_MODULE_EXT = '.dyn.py'


class Services(ServicesBase):

    def __init__(self):
        self.server_dir = os.path.abspath(os.path.dirname(__file__))
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../common/interface'))
        self.dynamic_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamic_modules'))
        ServicesBase.init_services(self)
        self.route_storage_module = route_storage.ThisModule()
        self._load_type_modules([
                'resource',
                'core',
                'packet',
                'param_editor',
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
#                'exception_test',
                ])
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.types.packet)
        self.modules = self.module_manager.modules
        self.module_manager.register_meta_hook()
        self.resources_loader = ResourcesLoader(self.types.resource,
                                                self.types.param_editor,
                                                iface_resources_dir=self.server_dir,
                                                client_modules_resources_dir=self.dynamic_module_dir)
        self._load_server_modules()
        Module.init_phases()
        self.route_storage = RouteStorage(route_storage.DbRouteRepository(self.route_storage_module))
        self.remoting = Remoting(self.iface_registry)
        self._register_transports()

    def _register_transports(self):
        for module in [tcp_transport, encrypted_transport]:
            module.register_transports(self.remoting.transport_registry, self)

    def _load_server_modules(self):
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
#                'exception_test',
                ]:
            fpath = os.path.join(self.server_dir, module_name + DYN_MODULE_EXT)
            with open(fpath) as f:
                source = f.read()
            package = 'hyperapp.server'
            module = self.types.packet.module(id=module_name, package=package, deps=[], satisfies=[], source=source, fpath=fpath)
            self.module_manager.load_code_module(module)
