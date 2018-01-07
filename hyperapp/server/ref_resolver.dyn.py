import logging
import os
import os.path

from ..common.interface import hyper_ref as href_types
from ..common.url import Url
from ..common.local_server_paths import LOCAL_REF_RESOLVER_URL_PATH, save_url_to_file
from .module import Module
from .command import command
from .object import Object

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'
REF_RESOLVER_CLASS_NAME = 'ref_resolver'


class RefResolver(Object):

    iface = href_types.ref_resolver
    class_name = REF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, server, ref_storage):
        Object.__init__(self)
        self._server = server
        self._ref_storage = ref_storage

    def resolve(self, path):
        path.check_empty()
        return self

    @command('resolve_ref')
    def command_resolve_ref(self, request):
        ref = request.params.ref
        referred = self._ref_storage.resolve_ref(ref)
        if not referred:
            raise href_types.unknown_ref_error(ref)
        return request.make_response_result(referred=referred)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._server = services.server
        self._tcp_server = services.tcp_server
        self._ref_storage = services.ref_storage

    def init_phase2(self):
        public_key = self._server.get_public_key()
        url = Url(RefResolver.iface, public_key, RefResolver.get_path())
        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
        url_path = save_url_to_file(url_with_routes, LOCAL_REF_RESOLVER_URL_PATH)
        log.info('Ref resolver url is saved to: %s', url_path)

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == RefResolver.class_name:
            return RefResolver(self._server, self._ref_storage).resolve(path)
        path.raise_not_found()
