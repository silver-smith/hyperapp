import logging

from ..common.ref import ref_repr, make_object_ref
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, save_bundle_to_file
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'
#REF_RESOLVER_CLASS_NAME = 'ref_resolver'


class RefResolver(object):

    def __init__(self):
        self._sources = []

    def resolve_ref(self, ref):
        log.debug('Resolving ref: %s', ref_repr(ref))
        for source in self._sources:
            capsule = source.resolve_ref(ref)
            if capsule:
                log.debug(' -> %r', capsule)
                return capsule
        return None

    def resolve_ref_recursive(self, rev):
        pass

    def add_source(self, source):
        self._sources.append(source)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_resolver = RefResolver()
