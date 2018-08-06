import logging
from pathlib import Path
import concurrent.futures

from ..common import cdr_coders, dict_coders  # self-registering
from ..common.route_storage import RouteStorage
from ..common.module_manager import ModuleManager
from ..common.services import ServicesBase
from .module import ModuleRegistry
from .resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


DYN_MODULE_EXT = '.dyn.py'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()


type_module_list = [
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
#    'server_management',
#    'code_repository',
#    'splitter',
#    'admin',
#    'object_selector',
#    'text_object',
#    'form',
#    'blog',
#    'module_list',
#    'test_list',
#    'exception_test',
    'fs',
    ]

code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_registry',
    'common.route_resolver',
    'common.tcp_packet',
    'common.ref_collector',
    'common.unbundler',
    'server.ponyorm_module',
    'server.ref_storage',
    'server.route_storage',
#    'server.client_code_repository',
#    'server.remoting',
#    'server.tcp_transport',
#    'server.encrypted_transport',
#    'server.tcp_server',
    'server.transport.registry',
    'server.request',
    'server.remoting',
    'server.transport.tcp',
    'server.transport.encrypted',
    'server.ref_resolver_service',
    'server.route_resolver_service',
    # 'server.form',
#    'server.admin',
#    'server.module_list',
    'server.server_management',
    'server.fs',
#    'server.blog',
#    'server.simple_text_object',
#    'server.sample_list',
#    'server.exception_test',
#    'server.hyperref_test',
    ]


class ServerServicesBase(ServicesBase):

    def __init__(self):
        super().__init__()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    def schedule_stopping(self):
        log.debug('Scheduling server stop...')
        self.thread_pool.submit(self.stop)

    def stop(self):
        log.debug('Stopping thread pool...')
        self.thread_pool.shutdown(wait=False)
        super().stop()


class Services(ServerServicesBase):

    def __init__(self, start_args):
        super().__init__()
        self.start_args = start_args
        self.server_dir = HYPERAPP_DIR / 'hyperapp' / 'server'
        self.dynamic_module_dir = HYPERAPP_DIR / 'dynamic_modules'
        ServicesBase.init_services(self)
        self.module_registry = ModuleRegistry()
        self.module_manager = ModuleManager(self, self.types, self.module_registry)
        self.modules = self.module_manager.modules
        self.module_manager.register_meta_hook()
        self._load_type_modules(type_module_list)
        self.resources_loader = ResourcesLoader(self.types.resource,
                                                self.types.param_editor,
                                                iface_resources_dir=self.server_dir,
                                                client_modules_resources_dir=self.dynamic_module_dir)
        self._load_server_modules()
        self.module_registry.init_phases()

    @property
    def is_running(self):
        return True
        #return self.tcp_server.is_running

    def _load_server_modules(self):
        for module_name in code_module_list:
            self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
