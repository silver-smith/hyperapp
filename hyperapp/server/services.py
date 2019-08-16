import logging
from pathlib import Path
import concurrent.futures

from ..common import cdr_coders, dict_coders  # self-registering
from ..common.services import ServicesBase

log = logging.getLogger(__name__)


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
#    'server_management',
#    'code_repository',
#    'splitter',
#    'admin',
    'text',
    'form',
    'blog',
#    'module_list',
#    'test_list',
#    'exception_test',
    'fs',
    ]

code_module_list = [
    'common.local_server_paths',
    'common.route_resolver',
    'common.tcp_packet',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.fs_service_impl',
    'server.ponyorm_module',
    'server.ref_storage',
#    'server.route_storage',
#    'server.client_code_repository',
#    'server.remoting',
#    'server.tcp_transport',
#    'server.encrypted_transport',
    'server.transport.registry',
    'server.request',
    'server.remoting',
    'server.remoting_proxy',
    'server.transport.tcp',
#    'server.transport.encrypted',
    'server.ref_resolver_service',
    'server.route_resolver_service',
    # 'server.form',
#    'server.admin',
#    'server.module_list',
    'server.server_management',
    'server.fs',
    'server.blog',
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
        self.server_dir = self.hyperapp_dir / 'server'
        self.init_services()
        self._load_type_module_list(type_module_list)
        try:
            self._load_code_module_list(code_module_list)
            self.module_registry.init_phases(self)
        except:
            self.stop()
            raise

    @property
    def is_running(self):
        return True
