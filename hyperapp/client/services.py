import os.path

# self-registering ifaces:
import hyperapp.common.interface.server_management
import hyperapp.common.interface.admin
import hyperapp.common.interface.fs
import hyperapp.common.interface.blog
import hyperapp.common.interface.article
import hyperapp.common.interface.module_list
# self-registering views:
import hyperapp.client.window
import hyperapp.client.tab_view
import hyperapp.client.narrower
import hyperapp.client.text_object
import hyperapp.client.proxy_list_object
import hyperapp.client.text_edit
import hyperapp.client.text_view
import hyperapp.client.form_view
import hyperapp.client.identity
import hyperapp.client.code_repository
import hyperapp.client.bookmarks
import hyperapp.client.url_clipboard

from ..common.htypes import iface_registry
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry
from . import code_repository
from .module_manager import ModuleManager
from .route_repository import FileRouteRepository, RouteStorage
from .identity import get_identity_controller

from hyperapp.client.transport import transport_registry
from . import tcp_transport
from . import encrypted_transport

from . import navigator
from . import splitter
from . import list_view


class Services(object):

    def __init__( self ):
        self.route_repo = RouteStorage(FileRouteRepository(os.path.expanduser('~/.local/share/hyperapp/client/routes')))
        self.code_repository = code_repository.get_code_repository()
        self.iface_registry = iface_registry
        self.objimpl_registry = objimpl_registry
        self.view_registry = view_registry
        self.module_mgr = ModuleManager(self)
        self.identity_controller = get_identity_controller()
        self.transport_registry = transport_registry
        self._register_transports()
        self._register_views()

    def _register_transports( self ):
        tcp_transport.register_transports(self.transport_registry, self)
        encrypted_transport.register_transports(self.transport_registry, self)

    def _register_views( self ):
        for module in [
                navigator,
                splitter,
                list_view,
                ]:
            module.register_views(self.view_registry, self)
