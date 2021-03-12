# reference registry: map refs to capsules

import logging

from .htypes import capsule_t
from .htypes.deduce_value_type import deduce_value_type
from .ref import ref_repr, make_capsule, make_ref
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Mosaic:

    def __init__(self, types):
        self._types = types
        self._registry = {}  # ref -> capsule

    def register_capsule(self, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule of type %s', ref_repr(ref), ref_repr(capsule.type_ref))
        existing_capsule = self._registry.get(ref)
        if existing_capsule:
            log.debug('  (already exists)')
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        self._registry[ref] = capsule
        return ref

    def put(self, piece, t=None):
        t = t or deduce_value_type(piece)
        log.debug('Registering piece %r: %s', t.name, piece)
        capsule = make_capsule(self._types, piece, t)
        ref = self.register_capsule(capsule)
        log.info('Registered piece %s: %s', ref_repr(ref), piece)
        return ref

    def put_opt(self, piece, t=None):
        if piece is None:
            return None
        return self.put(piece, t)

    def get(self, ref):
        return self._registry.get(ref)

    # Alias for web source.
    def pull(self, ref):
        return self.get(ref)
