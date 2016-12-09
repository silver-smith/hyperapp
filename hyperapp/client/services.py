import os.path


from ..common.htypes import tModule, tLocaleResources, iface_registry, builtin_type_registry
from ..common.type_repository import TypeRepository
from ..common.packet_coders import packet_coders
from ..common.route_storage import RouteStorage
from .objimpl_registry import ObjImplRegistry
from .view_registry import ViewRegistry
from .remoting import Remoting
from .named_url_file_repository import FileNamedUrlRepository
from .type_registry_registry import TypeRegistryRegistry
from .resources_manager import ResourcesRegistry, ResourcesManager
from .module_manager import ModuleManager
from .file_route_repository import FileRouteRepository
from .cache_repository import CacheRepository
from .proxy_registry import ProxyRegistry
from . import bookmarks
from .bookmarks import Bookmarks
from . import url_clipboard

from . import tcp_transport
from . import encrypted_transport

from . import navigator
from . import splitter
from . import list_view
from . import narrower

from . import proxy_object
from . import proxy_list_object


CACHE_DIR = os.path.expanduser('~/.cache/hyperapp/client')
CACHE_CONTENTS_ENCODING = 'json_pretty'
CACHE_FILE_EXT = '.json'
TYPE_MODULE_EXT = '.types'
DYN_MODULE_EXT = '.dyn.py'


class Services(object):

    def __init__( self ):
        self._dir = os.path.abspath(os.path.dirname(__file__))
        self.iface_registry = iface_registry
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../common/interface'))
        self.client_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.type_registry_registry = TypeRegistryRegistry(dict(builtins=builtin_type_registry()), self.iface_registry)
        self.type_repository = TypeRepository(self.interface_dir, self.iface_registry, self.type_registry_registry)
        self.route_storage = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.proxy_registry = ProxyRegistry()
        self.remoting = Remoting(self.route_storage, self.proxy_registry)
        self.objimpl_registry = ObjImplRegistry()
        self.view_registry = ViewRegistry(self.iface_registry, self.remoting)
        self.module_manager = ModuleManager(self)
        self.modules = self.module_manager.modules
        self.types = self.module_manager.types
        self.cache_repository = CacheRepository(CACHE_DIR, CACHE_CONTENTS_ENCODING, CACHE_FILE_EXT)
        self.resources_registry = ResourcesRegistry()
        self.resources_manager = ResourcesManager(self.resources_registry, self.cache_repository)
        self.module_manager.register_meta_hook()
        self._load_type_modules()
        self._load_modules()
        self.bookmarks = Bookmarks(FileNamedUrlRepository(
            self.iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/bookmarks')))
        self._register_modules()
        self._register_transports()
        self._load_resources()
        self._register_object_implementations()
        self._register_views()

    def _register_transports( self ):
        tcp_transport.register_transports(self.remoting.transport_registry, self)
        encrypted_transport.register_transports(self.remoting.transport_registry, self)

    def _load_type_modules( self ):
        for module_name in [
                'server_management',
                'code_repository',
                'splitter',
                'form',
                'text_object_types',
                ]:
            fpath = os.path.join(self.interface_dir, module_name + TYPE_MODULE_EXT)
            self.type_repository.load_module(module_name, fpath)

    def _register_modules( self ):
        for module in [
                splitter,
                bookmarks,
                url_clipboard,
            ]:
            module.__dict__['this_module'] = module.ThisModule(self)  # will auto-register itself

    def _load_modules( self ):
        for module_name in [
                'form',
                'code_repository',
                'identity',
                'text_object',
                'text_view',
                'text_edit',
                'form_view',
                ]:
            fpath = os.path.join(self.client_module_dir, module_name + DYN_MODULE_EXT)
            with open(fpath) as f:
                source = f.read()
            package = 'hyperapp.client'
            module = tModule(id=module_name, package=package, deps=[], satisfies=[], source=source, fpath=fpath)
            self.module_manager.add_code_module(module)

    def _load_resources( self ):
        for module in [
                'application',
                'window',
                'tab_view',
                'navigator',
                'code_repository',
                'code_repository_list',
                'identity_list',
                'bookmarks',
                'identity',
                'url_clipboard',
                'narrower',
                'history_list',
                'text_object',
                ]:
            with open(os.path.join(self._dir, '%s.resources.en.yaml' % module), 'rb') as f:
                try:
                    resources = packet_coders.decode('yaml', f.read(), tLocaleResources)
                except Exception as x:
                    raise RuntimeError('Error loading resource %r: %s' % (module, x))
                resource_id = ['client_module', module]
                self.resources_manager.register(resource_id, 'en', resources)

    def _register_object_implementations( self ):
        for module in [
                proxy_object,
                proxy_list_object,
                navigator,
                bookmarks,
                ]:
            module.register_object_implementations(self.objimpl_registry, self)

    def _register_views( self ):
        for module in [
                navigator,
                splitter,
                list_view,
                narrower,
                ]:
            module.register_views(self.view_registry, self)
