import logging

from .ref import ref_repr
from hyperapp.common.logger import log
from .module import Module

_log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'


class RefResolver(object):

    def __init__(self):
        self._sources = []

    def add_source(self, source):
        self._sources.append(source)

    def resolve_ref(self, ref):
        _log.debug('Resolving ref: %s', ref_repr(ref))
        for source in self._sources:
            capsule = source.resolve_ref(ref)
            if capsule:
                _log.info('Ref %s is resolved to capsule, type %s', ref_repr(ref), ref_repr(capsule.type_ref))
                return capsule
        _log.warning('Ref %s is failed to be resolved', ref_repr(ref))
        return None


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_resolver = RefResolver(services.types)
