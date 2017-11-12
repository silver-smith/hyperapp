import logging
import os
import os.path
from ..common.interface import hyper_ref as href_types
from ..common.interface import fs as fs_types
from ..common.url import Url
from ..common.local_server_paths import LOCAL_HREF_RESOLVER_URL_PATH, save_url_to_file
from .command import command
from .object import Object
from . import module as module_mod
from .fs import FsService

log = logging.getLogger(__name__)


MODULE_NAME = 'href_resolver'
HREF_RESOLVER_CLASS_NAME = 'href_resolver'


class HRefResolver(Object):

    iface = href_types.href_resolver
    class_name = HREF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, server):
        Object.__init__(self)
        self._server = server

    def resolve(self, path):
        path.check_empty()
        return self

    @command('resolve_href')
    def command_resolve_href(self, request):
        ref = request.params.ref
        assert ref == href_types.href('sha256', b'test-fs-href'), repr(ref)  # the only href currently supported
        fs_service_ref = href_types.service_ref('sha256', b'test-fs-service-ref')
        object = href_types.fs_ref(
            fs_service_ref=fs_service_ref,
            host='localhost',
            path=['usr', 'share'],
            current_file_name='dpkg',
            )
        return request.make_response_result(href_object=object)

    @command('resolve_service_ref')
    def command_resolve_service_ref(self, request):
        ref = request.params.ref
        assert ref == href_types.service_ref('sha256', b'test-fs-service-ref'), repr(ref)  # the only service ref currently supported
        fs_service_url = Url(fs_types.fs_service, self._server.get_public_key(), FsService.get_path())
        service = href_types.fs_service(
            service_url=fs_service_url.to_data())
        return request.make_response_result(service=service)


class ThisModule(module_mod.Module):

    def __init__(self, services):
        module_mod.Module.__init__(self, MODULE_NAME)
        self._server = services.server
        self._tcp_server = services.tcp_server

    def init_phase2(self):
        public_key = self._server.get_public_key()
        url = Url(HRefResolver.iface, public_key, HRefResolver.get_path())
        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
        url_path = save_url_to_file(url_with_routes, LOCAL_HREF_RESOLVER_URL_PATH)
        log.info('HRef resolver url is saved to: %s', url_path)

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == HRefResolver.class_name:
            return HRefResolver(self._server).resolve(path)
        path.raise_not_found()
