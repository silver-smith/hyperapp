import os.path
import logging
from ..common.route_storage import RouteStorage
from ..common.module_manager import ModuleManager
from ..common.services import ServicesBase
from .module import ModuleRegistry
from .server import Server
from .resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


DYN_MODULE_EXT = '.dyn.py'


class Services(ServicesBase):

    def __init__(self, start_args):
        self.start_args = start_args
        self.server_dir = os.path.abspath(os.path.dirname(__file__))
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../common/interface'))
        self.dynamic_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamic_modules'))
        ServicesBase.init_services(self)
        self.module_registry = ModuleRegistry()
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.module_registry)
        self.modules = self.module_manager.modules
        self.module_manager.register_meta_hook()
        self._load_type_modules([
            'error',
            'resource',
            'core',
            'hyper_ref',
            'packet',
            'ref_list',
            'param_editor',
            'server_management',
            'code_repository',
            'splitter',
            'admin',
            'object_selector',
            'text_object',
            'form',
            'blog',
            'module_list',
            'test_list',
            'exception_test',
            'fs',
            ])
        self.resources_loader = ResourcesLoader(self.types.resource,
                                                self.types.param_editor,
                                                iface_resources_dir=self.server_dir,
                                                client_modules_resources_dir=self.dynamic_module_dir)
        self.server = Server.create(self, start_args)
        self._load_server_modules()
        self.module_registry.init_phases()

    def start(self):
        self.tcp_server.start()

    @property
    def is_running(self):
        return self.tcp_server.is_running

    def stop(self):
        self.tcp_server.stop()

    def _load_server_modules(self):
        for module_name in [
                'ponyorm_module',
                'ref_storage',
                'route_storage',
                'client_code_repository',
                'remoting',
                'tcp_transport',
                'encrypted_transport',
                'tcp_server',
                'ref_resolver',
#                'form',
                'admin',
                'module_list',
                'server_management',
                'fs',
                'blog',
                'simple_text_object',
                'sample_list',
                'exception_test',
                'hyperref_test',
                ]:
            fpath = os.path.join(self.server_dir, module_name + DYN_MODULE_EXT)
            with open(fpath) as f:
                source = f.read()
            package = 'hyperapp.server'
            module = self.types.packet.module(id=module_name, package=package, deps=[], satisfies=[], source=source, fpath=fpath)
            self.module_manager.load_code_module(module)
