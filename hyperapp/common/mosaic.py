# reference registry: map refs to capsules

import logging
from collections import namedtuple

from .htypes import capsule_t
from .htypes.deduce_value_type import deduce_value_type
from .ref import DecodedCapsule, decode_capsule, make_capsule, make_ref
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Mosaic:

    _Rec = namedtuple('_Rec', 'type_ref t value')

    def __init__(self, types):
        self._types = types
        self._ref_to_capsule = {}  # ref -> capsule
        self._ref_to_rec = {}  # ref -> _Rec
        self._piece_to_ref = {}

    def register_capsule(self, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule of type %s', ref, capsule.type_ref)
        existing_capsule = self._ref_to_capsule.get(ref)
        if existing_capsule:
            log.debug('  (already exists)')
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        dc = decode_capsule(self._types, capsule)
        self._ref_to_capsule[ref] = capsule
        self._ref_to_rec[ref] = self._Rec(dc.type_ref, dc.t, dc.value)
        self._piece_to_ref[dc.value] = ref
        return ref

    def put(self, piece, t=None):
        try:
            return self._piece_to_ref[piece]
        except KeyError:
            pass
        t = t or deduce_value_type(piece)
        log.debug('Registering piece %r: %s', t.name, piece)
        capsule = make_capsule(self._types, piece, t)
        ref = self.register_capsule(capsule)
        log.debug('Registered piece %s (type: %s): %r', ref, capsule.type_ref, piece)
        return ref

    def put_opt(self, piece, t=None):
        if piece is None:
            return None
        return self.put(piece, t)

    def get(self, ref):
        return self._ref_to_capsule.get(ref)

    # Alias for web source.
    def pull(self, ref):
        return self.get(ref)

    def resolve_ref(self, ref, expected_type=None) -> DecodedCapsule:
        try:
            return self._ref_to_rec[ref]
        except KeyError:
            pass
        capsule = self.get(ref)
        assert capsule is not None, f"Unknown ref: {ref}"
        return decode_capsule(self._types, capsule, expected_type)
