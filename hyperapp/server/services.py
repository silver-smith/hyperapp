import logging
from pathlib import Path

from ..common import cdr_coders  # self-registering
from ..common.services import Services

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
    'object_type',
    'layout',
    'text',
    'form',
    'blog',
#    'module_list',
#    'test_list',
#    'exception_test',
    'fs',
    ]

code_module_list = [
    'common.dict_coders',
    'common.local_server_paths',
    'common.route_resolver',
    'common.tcp_packet',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.fs_service_impl',
    'server.async_stop',
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


class ServerServices(Services):

    def __init__(self, start_args):
        super().__init__()
        self.init_services()
        try:
            self.init_modules(type_module_list, code_module_list)
        except:
            self.stop()
            raise

    @property
    def is_running(self):
        return True
