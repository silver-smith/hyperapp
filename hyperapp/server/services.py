import logging
from pathlib import Path

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
        self.server_dir = Path(__file__).parent.resolve()
        self.hyperapp_dir = self.server_dir.parent
        self.interface_dir = Path(__file__).parent.joinpath('../common/interface').resolve()
        self.dynamic_module_dir = Path(__file__).parent.joinpath('../../dynamic_modules').resolve()
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
            'module',
            'packet',
            'tcp_transport',
            'encrypted_transport',
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
                'server.ponyorm_module',
                'server.ref_storage',
                'common.ref_registry',
                'server.route_storage',
                'server.client_code_repository',
                'server.remoting',
                'server.tcp_transport',
                'server.encrypted_transport',
                'server.tcp_server',
                'server.transport.tcp',
                'server.transport.encrypted',
                'common.ref_collector',
                'server.ref_resolver',
#                'server.form',
                'server.admin',
                'server.module_list',
                'server.server_management',
                'server.fs',
                'server.blog',
                'server.simple_text_object',
                'server.sample_list',
                'server.exception_test',
                'server.hyperref_test',
                ]:
            self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
