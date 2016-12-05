import os.path

# self-registering ifaces:
import hyperapp.common.interface.server_management

from ..common.htypes import tLocaleResources, iface_registry
from ..common.type_repository import TypeRepository
from ..common.packet_coders import packet_coders
from ..common.route_storage import RouteStorage
from .objimpl_registry import ObjImplRegistry
from .view_registry import ViewRegistry
from .remoting import Remoting
from .named_url_file_repository import FileNamedUrlRepository
from .type_registry_registry import TypeRegistryRegistry
from . import code_repository
from .code_repository import CodeRepository
from .resources_manager import ResourcesRegistry, ResourcesManager
from .module_manager import ModuleManager
from .file_route_repository import FileRouteRepository
from . import identity
from .identity import FileIdentityRepository, IdentityController
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
from . import text_view
from . import text_edit
from . import form_view

from . import text_object
from . import proxy_object
from . import proxy_list_object


CACHE_DIR = os.path.expanduser('~/.cache/hyperapp/client')
CACHE_CONTENTS_ENCODING = 'json_pretty'
CACHE_FILE_EXT = '.json'


class Services(object):

    def __init__( self ):
        self._dir = os.path.abspath(os.path.dirname(__file__))
        self.iface_registry = iface_registry
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../common/interface'))
        self.type_registry_registry = TypeRegistryRegistry(self.iface_registry)
        self.type_repository = TypeRepository(self.interface_dir, self.iface_registry, self.type_registry_registry)
        self.route_storage = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.proxy_registry = ProxyRegistry()
        self.remoting = Remoting(self.route_storage, self.proxy_registry)
        self.objimpl_registry = ObjImplRegistry()
        self.view_registry = ViewRegistry(self.remoting)
        self.module_mgr = ModuleManager(self)
        self.identity_controller = IdentityController(FileIdentityRepository(os.path.expanduser('~/.local/share/hyperapp/client/identities')))
        self.cache_repository = CacheRepository(CACHE_DIR, CACHE_CONTENTS_ENCODING, CACHE_FILE_EXT)
        self.code_repository = CodeRepository(
            self.iface_registry, self.remoting, self.cache_repository,
            FileNamedUrlRepository(iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/code_repositories')))
        self.resources_registry = ResourcesRegistry()
        self.resources_manager = ResourcesManager(self.resources_registry, self.cache_repository)
        self.bookmarks = Bookmarks(FileNamedUrlRepository(
            self.iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/bookmarks')))
        self.module_mgr.register_meta_hook()
        self._register_transports()
        self._register_modules()
        self._load_resources()
        self._register_object_implementations()
        self._register_views()

    def _register_transports( self ):
        tcp_transport.register_transports(self.remoting.transport_registry, self)
        encrypted_transport.register_transports(self.remoting.transport_registry, self)

    def _register_modules( self ):
        for module in [
            identity,
            code_repository,
            bookmarks,
            url_clipboard,
            ]:
            module.ThisModule(self)  # will auto-register itself

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
                text_object,
                proxy_object,
                proxy_list_object,
                navigator,
                code_repository,
                identity,
                bookmarks,
                ]:
            module.register_object_implementations(self.objimpl_registry, self)

    def _register_views( self ):
        for module in [
                navigator,
                splitter,
                list_view,
                narrower,
                text_view,
                text_edit,
                form_view,
                ]:
            module.register_views(self.view_registry, self)
