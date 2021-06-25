import logging

from hyperapp.common.htypes.packet_coders import packet_coders

_log = logging.getLogger(__name__)


class RefResolveFailure(Exception):

    def __init__(self, ref):
        super().__init__(f"Failed to resolve ref {ref}")


class Web(object):

    def __init__(self, types):
        self._types = types
        self._sources = []

    def add_source(self, source):
        self._sources.append(source)

    def pull(self, ref):
        _log.debug('Resolving ref: %s', ref)
        for source in self._sources:
            capsule = source.pull(ref)
            if capsule:
                _log.debug('Ref %s is resolved to capsule, type %s', ref, capsule.type_ref)
                return capsule
        raise RefResolveFailure(ref)

    def summon(self, ref, expected_type=None):
        capsule = self.pull(ref)
        t = self._types.resolve(capsule.type_ref)
        if expected_type:
            assert t is expected_type, (t, expected_type)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
