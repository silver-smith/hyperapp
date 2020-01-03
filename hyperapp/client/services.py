import os.path
from pathlib import Path

from ..common.htypes.packet_coders import packet_coders
from ..common.ref import phony_ref
from ..common.route_storage import RouteStorage
from ..common.services import ServicesBase
from ..common.module import ModuleRegistry
from .file_route_repository import FileRouteRepository
from .cache_repository import CacheRepository
from .proxy_registry import ProxyRegistry


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
    'layout_editor',
    'splitter',
    'tab_view',
    'navigator',
    'menu_bar',
    'command_pane',
    'window',
    'root_layout',
    'application_state',
    # 'server_management',
    # 'code_repository',
    'text',
    'form',
    'record_view',
    'ref_list',
    'line',
    # 'narrower',
    'master_details',
    'fs',
    'blog',
    'tree_view',
    'tree_to_list_adapter',
    'data_viewer',
    'log_viewer',
    'list_view_sample',
    'tree_view_sample',
    ]

code_module_list = [
    'common.local_server_paths',
    'common.route_resolver',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.tcp_packet',
    'common.resource_registry',
    'common.resource_resolver',
    'common.resource_loader',
    'common.fs_service_impl',
    'client.module_command_registry',
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
    'client.objimpl_registry',
    'client.object_registry',
    'client.layout_registry',
    'client.view',
    'client.composite',
    'client.column',
    'client.list_object',
    'client.tree_object',
    # 'client.splitter',
    'client.command_hub',
    'client.view_registry',
    'client.view_handler',
    'client.default_state_builder',
    'client.layout_manager',
    'client.layout_editor',
    'client.tab_view',
    'client.menu_bar',
    'client.command_pane',
    'client.window',
    # 'client.navigator.history_list',
    'client.navigator.navigator',
    # 'client.navigator.module',
    # 'client.form',
    # 'code_repository',
    # 'identity',
    # 'redirect_handle',
    # 'form_view',
    # 'client.error_handler_impl',
    # 'bookmarks',
    # 'client.ref_redirect_handle',
    # 'client.line_list_panel',
    # 'client.narrower',
    # 'client.url_clipboard',
    'client.text_object',
    'client.data_viewer',
    'client.log_viewer',
    'client.application_state_storage',
    'client.master_details',
    'client.line_edit',
    'client.text_view',
    'client.text_edit',
    'client.items_view',
    'client.list_view',
    'client.list_view_sample',
    'client.tree_view',
    'client.tree_view_sample',
    'client.tree_to_list_adapter',
    'client.tree_to_list_adapter_sample',
    'client.fs',
    'client.fs_local_service',
    'client.fs_remote_service',
    'client.ref_list',
    'client.local_server_ref_list',
    'client.wiki_text_sample',
    'client.record_object',
    'client.record_view',
    'client.blog',
    ]


class ClientServicesBase(ServicesBase):

    def init_services(self):
        super().init_services()
        self.logger.init_asyncio_task_factory()

    def schedule_stopping(self):
        assert 0  # todo


class Services(ClientServicesBase):

    def __init__(self, event_loop):
        super().__init__()
        self.event_loop = event_loop
        self._hyperapp_client_dir = self.hyperapp_dir / 'client'
        self.client_resources_dir = self._hyperapp_client_dir
        self.init_services()
        self.client_module_dir = self._hyperapp_client_dir
        self.module_registry = ModuleRegistry()
        self.route_storage = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.proxy_registry = ProxyRegistry()
        self._load_type_module_list(type_module_list)
        #self.remoting = Remoting(self.types.resource, self.types.packet, self.iface_registry, self.route_storage, self.proxy_registry)
        self.cache_repository = CacheRepository(CACHE_DIR, CACHE_CONTENTS_ENCODING, CACHE_FILE_EXT)
        self._load_code_module_list(code_module_list)
        # enable application resources to work; todo: move application commands to dynamic module
        self.local_code_module_registry.register('client.application', phony_ref('application'))
        self.module_registry.init_phases(self)
        #self._register_transports()

    async def async_init(self):
        for method in self.module_registry.enum_modules_method('async_init'):
            await method(self)

    def _register_transports(self):
        tcp_transport.register_transports(self.remoting.transport_registry, self)
        encrypted_transport.register_transports(self.remoting.transport_registry, self)
