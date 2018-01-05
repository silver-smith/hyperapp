import logging
import os
import os.path

from pony.orm import db_session, Required, PrimaryKey

from ..common.interface import hyper_ref as href_types
from ..common.interface import ref_list as ref_list_types
from ..common.url import Url
from ..common.packet_coders import packet_coders
from ..common.referred import make_referred, make_ref
from ..common.local_server_paths import LOCAL_REF_RESOLVER_URL_PATH, save_url_to_file
from .command import command
from .object import Object
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'
REF_RESOLVER_CLASS_NAME = 'ref_resolver'
DEFAULT_ENCODING = 'cdr'


class RefStorage(object):

    @db_session
    def resolve_ref(self, ref):
        rec = this_module.Ref.get(ref=ref)
        if not rec:
            return None
        return href_types.referred(
            full_type_name=rec.full_type_name.split('.'),
            hash_algorithm=rec.hash_algorithm,
            encoding=rec.encoding,
            encoded_object=rec.encoded_object,
            )

    @db_session
    def store_ref(self, ref, referred):
        rec = this_module.Ref.get(ref=ref)
        if rec:
            rec.full_type_name = '.'.join(referred.full_type_name)
            rec.hash_algorithm = referred.hash_algorithm
            rec.encoding = referred.encoding
            rec.encoded_object = referred.encoded_object
        else:
            rec = this_module.Ref(
                ref=ref,
                full_type_name='.'.join(referred.full_type_name),
                hash_algorithm=referred.hash_algorithm,
                encoding=referred.encoding,
                encoded_object=referred.encoded_object,
                )

    def add_object(self, t, object):
        referred = make_referred(t, object)
        ref = make_ref(referred)
        self.store_ref(ref, referred)
        return ref


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


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._server = services.server
        self._tcp_server = services.tcp_server
        services.ref_storage = self.ref_storage = RefStorage()

    def init_phase2(self):
        self.Ref = self.make_entity(
            'Ref',
            ref=PrimaryKey(bytes),
            full_type_name=Required(str),
            hash_algorithm=Required(str),
            encoding=Required(str),
            encoded_object=Required(bytes),
            )
        public_key = self._server.get_public_key()
        url = Url(RefResolver.iface, public_key, RefResolver.get_path())
        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
        url_path = save_url_to_file(url_with_routes, LOCAL_REF_RESOLVER_URL_PATH)
        log.info('Ref resolver url is saved to: %s', url_path)

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == RefResolver.class_name:
            return RefResolver(self._server, self.ref_storage).resolve(path)
        path.raise_not_found()
