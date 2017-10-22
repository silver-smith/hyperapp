import logging
from ..common.interface import hyper_ref as hyper_ref_types
from ..common.url import Url
from .object import Object
from . import module as module_mod

log = logging.getLogger(__name__)


MODULE_NAME = 'href_resolver'
HREF_RESOLVER_CLASS_NAME = 'href_resolver'


class HRefResolver(Object):

    iface = hyper_ref_types.href_resolver
    class_name = HREF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self):
        Object.__init__(self)

    def resolve(self, path):
        path.check_empty()
        return self


class ThisModule(module_mod.Module):

    def __init__(self, services):
        module_mod.Module.__init__(self, MODULE_NAME)
        self._server = services.server
        self._tcp_server = services.tcp_server

    def init_phase2(self):
        public_key = self._server.get_public_key()
        url = Url(HRefResolver.iface, public_key, HRefResolver.get_path())
        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
        log.info('HRef resolver url: %s', url_with_routes.to_str())

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == HRefResolver.class_name:
            return HRefResolver().resolve(path)
        path.raise_not_found()
