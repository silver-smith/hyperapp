import logging

from .util import full_type_name_to_str
from .htypes.packet_coders import packet_coders
from .ref import ref_repr
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_resolver'


class RefResolver(object):

    def __init__(self, types):
        self._types = types
        self._sources = []

    def add_source(self, source):
        self._sources.append(source)

    def resolve_ref(self, ref):
        log.debug('Resolving ref: %s', ref_repr(ref))
        for source in self._sources:
            capsule = source.resolve_ref(ref)
            if capsule:
                log.debug(' -> %r', capsule)
                return capsule
        return None

    def resolve_ref_to_object(self, ref, expected_type=None):
        capsule = self.resolve_ref(ref)
        assert capsule is not None, 'Unknown ref: %s' % ref_repr(ref)
        if expected_type:
            assert full_type_name_to_str(capsule.full_type_name) == expected_type
        t = self._types.resolve(capsule.full_type_name)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_resolver = RefResolver(services.types)
