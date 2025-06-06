import logging

from hyperapp.boot.htypes.packet_coders import packet_coders

_log = logging.getLogger(__name__)


class RefResolveFailure(Exception):

    def __init__(self, ref):
        super().__init__(f"Failed to resolve ref: {ref}")


class Web(object):

    def __init__(self, mosaic, pyobj_creg):
        self._mosaic = mosaic
        self._pyobj_creg = pyobj_creg
        self._sources = []

    def add_source(self, source):
        self._sources.append(source)

    def pull(self, ref):
        _log.debug('Resolving ref: %s', ref)
        for source in [self._mosaic] + self._sources:
            capsule = source.pull(ref)
            if capsule:
                _log.debug('Ref %s is resolved to capsule, type %s', ref, capsule.type_ref)
                return capsule
        raise RefResolveFailure(ref)

    def summon_with_t(self, ref, expected_type=None):
        try:
            rec = self._mosaic.resolve_ref(ref)
        except KeyError:
            pass
        else:
            return (rec.value, rec.t)
        capsule = self.pull(ref)
        # Following code is actually dead.
        t = self._pyobj_creg.invite(capsule.type_ref)
        if expected_type:
            assert t is expected_type, (t, expected_type)
        value = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        return (value, t)

    def summon_with_t_opt(self, ref, expected_type=None):
        if ref is None:
            return (None, None)
        return self.summon_with_t(ref, expected_type)

    def summon(self, ref, expected_type=None):
        value, t = self.summon_with_t(ref, expected_type)
        return value

    def summon_opt(self, ref):
        if ref is None:
            return None
        return self.summon(ref)
