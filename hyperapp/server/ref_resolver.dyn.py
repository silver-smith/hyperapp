import logging

from ..common.interface import hyper_ref as href_types
from ..common.ref import ref_repr, make_object_ref
from ..common.url import Url
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, save_parcel_to_file
from .command import command
from .object import Object

log = logging.getLogger(__name__)


#REF_RESOLVER_CLASS_NAME = 'ref_resolver'


class RefResolver(Object):

    iface = href_types.ref_resolver
    #class_name = REF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, ref_registry, ref_storage):
        Object.__init__(self)
        self._ref_registry = ref_registry
        self._ref_storage = ref_storage

    def resolve(self, path):
        path.check_empty()
        return self

    @command('resolve_ref')
    def command_resolve_ref(self, request, ref):
        referred = self.resolve_ref(ref)
        if not referred:
            raise href_types.unknown_ref_error(ref)
        return request.make_response_result(referred=referred)

    def resolve_ref(self, ref):
        log.debug('Resolving ref: %s', ref_repr(ref))
        referred = self._ref_registry.resolve_ref(ref)
        if not referred:
            referred = self._ref_storage.resolve_ref(ref)
        return referred

    def resolve_ref_recursive(self, rev):
        pass
