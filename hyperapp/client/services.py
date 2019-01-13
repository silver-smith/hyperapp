import os.path
from pathlib import Path

from ..common.htypes.packet_coders import packet_coders
from ..common.route_storage import RouteStorage
from ..common.services import ServicesBase
from ..common.module import ModuleRegistry
from .file_route_repository import FileRouteRepository
from .cache_repository import CacheRepository
from .proxy_registry import ProxyRegistry
from . import url_clipboard

from . import command
from . import list_view


CACHE_DIR = os.path.expanduser('~/.cache/hyperapp/client')
CACHE_CONTENTS_ENCODING = 'json'
CACHE_FILE_EXT = '.json'
TYPE_MODULE_EXT = '.types'


type_module_list = [
    'error',
    'resource',
    'core',
    'hyper_ref',
    'module',
    'packet',
    'tcp_transport',
    'splitter',
    'tab_view',
    'navigator',
    'window',
    'param_editor',
#    'server_management',
#    'code_repository',
    'text_object',
    'form',
    'ref_list',
    'line_object',
    'narrower',
    'fs',
    'object_selector',
    'blog',
    ]

code_module_list = [
    'common.visual_rep_encoders',
    'common.local_server_paths',
    'common.route_resolver',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.tcp_packet',
    'common.resources_loader',
    'common.fs_service_impl',
    'client.async_ref_resolver',
    'client.async_capsule_registry',
    'client.async_route_resolver',
    'client.endpoint_registry',
    'client.service_registry',
    'client.transport.registry',
    'client.request',
    'client.remoting',
    'client.remoting_proxy',
    'client.transport.tcp',
    'client.remote_ref_resolver',
    'client.remote_route_resolver',
    'client.resources_manager',
    'client.objimpl_registry',
    'client.view_registry',
    'client.splitter',
    'client.tab_view',
    'client.window',
    'client.navigator.history_list',
    'client.navigator.navigator',
    'client.navigator.module',
    'client.list_view_module',
    'client.form',
#    'code_repository',
#    'identity',
#    'redirect_handle',
    'client.text_object',
    'client.text_view',
    'client.text_edit',
    #                'form_view',
    'client.error_handler_impl',
#    'bookmarks',
#    'client.ref_redirect_handle',
    'client.line_edit',
    'client.line_list_panel',
    'client.narrower',
    'client.handle_resolver',
    'client.ref_list',
    'client.local_server_ref_list',
    'client.fs',
    'client.fs_local_service',
    'client.fs_remote_service',
    'client.object_selector',
    'client.blog',
    'client.default_state_builder',
    ]


class ClientServicesBase(ServicesBase):

    def schedule_stopping(self):
        assert 0  # todo


class Services(ClientServicesBase):

    def __init__(self, event_loop):
        super().__init__()
        self.event_loop = event_loop
        self._hyperapp_client_dir = self.hyperapp_dir / 'client'
        self.client_resources_dir = self._hyperapp_client_dir
        ServicesBase.init_services(self)
        self.client_module_dir = self._hyperapp_client_dir
        self.module_registry = ModuleRegistry()
        self.route_storage = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.proxy_registry = ProxyRegistry()
        self._load_type_module_list(type_module_list)
        #self.remoting = Remoting(self.types.resource, self.types.packet, self.iface_registry, self.route_storage, self.proxy_registry)
        self.cache_repository = CacheRepository(CACHE_DIR, CACHE_CONTENTS_ENCODING, CACHE_FILE_EXT)
        self._load_code_module_list(code_module_list)
        self._register_static_modules()
        #self._register_transports()

    async def async_init(self):
        await self.module_registry.async_init(self)

    def _register_static_modules(self):
        for module in [
                url_clipboard,
            ]:
            this_module = module.ThisModule(self)
            module.__dict__['this_module'] = this_module
            self.module_registry.register(this_module)

    def _register_transports(self):
        tcp_transport.register_transports(self.remoting.transport_registry, self)
        encrypted_transport.register_transports(self.remoting.transport_registry, self)
