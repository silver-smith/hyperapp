import os.path
from pathlib import Path

from ..common.htypes.packet_coders import packet_coders
from ..common.route_storage import RouteStorage
from ..common.services import ServicesBase
from .objimpl_registry import ObjImplRegistry
from .view_registry import ViewRegistry
from .param_editor_registry import ParamEditorRegistry
#from .remoting import Remoting
from .resources_manager import ResourcesRegistry, ResourcesManager
from .module_manager import ModuleManager
from .module import ClientModuleRegistry
from .file_route_repository import FileRouteRepository
from .cache_repository import CacheRepository
from .proxy_registry import ProxyRegistry
from . import url_clipboard

#from . import tcp_transport
#from . import encrypted_transport

from . import command
from . import tab_view
from . import window
from . import navigator
from . import splitter
from . import list_view

from . import proxy_object


HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()
CACHE_DIR = os.path.expanduser('~/.cache/hyperapp/client')
CACHE_CONTENTS_ENCODING = 'json'
CACHE_FILE_EXT = '.json'
TYPE_MODULE_EXT = '.types'
DYN_MODULE_EXT = '.dyn.py'


type_module_list = [
    'error',
    'resource',
    'core',
    'hyper_ref',
    'module',
    'packet',
    'tcp_transport',
    'param_editor',
#    'server_management',
#    'code_repository',
    'splitter',
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
    'common.ref',
    'common.ref_resolver',
    'common.ref_registry',
    'common.route_resolver',
    'common.ref_collector',
    'common.unbundler',
    'common.tcp_packet',
    'client.async_ref_resolver',
    'client.capsule_registry',
    'client.async_route_resolver',
    'client.endpoint_registry',
    'client.transport.registry',
    'client.remoting',
    'client.remoting_proxy',
    'client.transport.tcp',
    'client.remote_ref_resolver',
    'client.remote_route_resolver',
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
    ]


class ClientServicesBase(ServicesBase):

    def schedule_stopping(self):
        assert 0  # todo


class Services(ClientServicesBase):

    def __init__(self, event_loop):
        super().__init__()
        self.event_loop = event_loop
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self._hyperapp_client_dir = HYPERAPP_DIR / 'hyperapp' / 'client'
        ServicesBase.init_services(self)
        self.client_module_dir = self._hyperapp_client_dir
        self.module_registry = ClientModuleRegistry()
        self.route_storage = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.proxy_registry = ProxyRegistry()
        self.module_manager = ModuleManager(self)
        self.modules = self.module_manager.modules
        self.module_manager.register_meta_hook()
        self._load_type_modules(type_module_list)
        self.objimpl_registry = ObjImplRegistry('object')
        #self.remoting = Remoting(self.types.resource, self.types.packet, self.iface_registry, self.route_storage, self.proxy_registry)
        self.view_registry = ViewRegistry(self.module_registry)
        self.param_editor_registry = ParamEditorRegistry()
        self.module_manager.init_types(self)
        self.cache_repository = CacheRepository(CACHE_DIR, CACHE_CONTENTS_ENCODING, CACHE_FILE_EXT)
        self.view_registry.set_core_types(self.types.core)
        self.resources_registry = ResourcesRegistry(self.types.resource)
        self.resources_manager = ResourcesManager(
            self.types.resource, self.types.param_editor, self.resources_registry, self.cache_repository, self._hyperapp_client_dir)
        self._load_code_modules()
        self._register_static_modules()
        #self._register_transports()
        self._register_object_implementations()
        self._register_views()

    async def async_init(self):
        await self.module_registry.async_init(self)

    def _register_static_modules(self):
        for module in [
                navigator,
                tab_view,
                window,
                splitter,
                url_clipboard,
            ]:
            this_module = module.ThisModule(self)
            module.__dict__['this_module'] = this_module
            self.module_registry.register(this_module)

    def _register_transports(self):
        tcp_transport.register_transports(self.remoting.transport_registry, self)
        encrypted_transport.register_transports(self.remoting.transport_registry, self)

    def _load_code_modules(self):
        for module_name in code_module_list:
            self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)

    def _register_object_implementations(self):
        for module in [
                #proxy_object,
                navigator,
                ]:
            module.register_object_implementations(self.objimpl_registry, self)

    def _register_views(self):
        for module in [
                navigator,
                splitter,
                list_view,
                ]:
            module.register_views(self.view_registry, self)
