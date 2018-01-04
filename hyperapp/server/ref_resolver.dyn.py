import logging
import os
import os.path
from ..common.interface import hyper_ref as href_types
from ..common.interface import fs as fs_types
from ..common.interface import blog as blog_types
from ..common.interface import ref_list as ref_list_types
from ..common.url import Url
from ..common.packet_coders import packet_coders
from ..common.local_server_paths import LOCAL_REF_RESOLVER_URL_PATH, save_url_to_file
from .command import command
from .object import Object
from . import module as module_mod
from .fs import FsService
from .blog import BlogService
from .server_management import RefListResolverService

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'
REF_RESOLVER_CLASS_NAME = 'ref_resolver'
DEFAULT_ENCODING = 'cdr'


class RefResolver(Object):

    iface = href_types.ref_resolver
    class_name = REF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, server):
        Object.__init__(self)
        self._server = server

    def resolve(self, path):
        path.check_empty()
        return self

    @command('resolve_ref')
    def command_resolve_ref(self, request):
        ref = request.params.ref
        if ref == b'server-ref-list':
            service_ref = b'ref-list-service'
            object = ref_list_types.dynamic_ref_list(
                ref_list_service=service_ref,
                ref_list_id='server-management',
                )
            referred = self._encode_referred(ref_list_types.dynamic_ref_list, object)
            return request.make_response_result(referred=referred)
        if ref == b'ref-list-service':
            service_url = Url(RefListResolverService.iface, self._server.get_public_key(), RefListResolverService.get_path())
            object = ref_list_types.ref_list_service(
                service_url=service_url.to_data())
            referred = self._encode_referred(ref_list_types.ref_list_service, object)
            return request.make_response_result(referred=referred)
        if ref == b'test-fs-ref':
            fs_service_ref = b'test-fs-service-ref'
            object = fs_types.fs_ref(
                fs_service_ref=fs_service_ref,
                host='localhost',
                path=['usr', 'share'],
                current_file_name='dpkg',
                )
            return request.make_response_result(ref_object=object)
        if ref == b'test-blog-ref':
            blog_service_ref = b'test-blog-service-ref'
            object = blog_types.blog_ref(
                blog_service_ref=blog_service_ref,
                blog_id='test-blog',
                current_article_id=None,
                )
            return request.make_response_result(ref_object=object)
        if ref == b'test-fs-service-ref':
            fs_service_url = Url(fs_types.fs_service_iface, self._server.get_public_key(), FsService.get_path())
            service = fs_types.fs_service(
                service_url=fs_service_url.to_data())
            return request.make_response_result(service=service)
        if ref == b'test-blog-service-ref':
            blog_service_url = Url(blog_types.blog_service_iface, self._server.get_public_key(), BlogService.get_path())
            service = blog_types.blog_service(
                service_url=blog_service_url.to_data())
            return request.make_response_result(service=service)
        raise href_types.unknown_ref_error(ref)

    def _encode_referred(self, t, object):
        hash_algorithm = 'dummy'
        encoding = DEFAULT_ENCODING
        encoded_object = packet_coders.encode(encoding, object, t)
        return href_types.referred(t.full_name, hash_algorithm, encoding, encoded_object)


class ThisModule(module_mod.Module):

    def __init__(self, services):
        module_mod.Module.__init__(self, MODULE_NAME)
        self._server = services.server
        self._tcp_server = services.tcp_server

    def init_phase2(self):
        public_key = self._server.get_public_key()
        url = Url(RefResolver.iface, public_key, RefResolver.get_path())
        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
        url_path = save_url_to_file(url_with_routes, LOCAL_REF_RESOLVER_URL_PATH)
        log.info('Ref resolver url is saved to: %s', url_path)

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == RefResolver.class_name:
            return RefResolver(self._server).resolve(path)
        path.raise_not_found()
