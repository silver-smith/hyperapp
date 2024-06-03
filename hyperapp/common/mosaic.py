# reference registry: map refs to capsules

import logging
from collections import namedtuple

from .htypes import capsule_t
from .htypes.deduce_value_type import deduce_value_type
from .ref import DecodedCapsule, decode_capsule, make_capsule, make_ref
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Mosaic:

    _Rec = namedtuple('_Rec', 'capsule type_ref t value')

    def __init__(self, pyobj_creg):
        self._pyobj_creg = pyobj_creg
        self._ref_to_rec = {}  # ref -> _Rec
        self._piece_to_ref = {}

    def register_capsule(self, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule of type %s', ref, capsule.type_ref)
        rec = self._ref_to_rec.get(ref)
        if rec:
            log.debug('  (already exists)')
            assert capsule == rec.capsule, repr((rec.capsule, capsule))  # new capsule does not match existing one
            return
        dc = decode_capsule(self._pyobj_creg, capsule)
        self._register_capsule(ref, capsule, dc.type_ref, dc.t, dc.value)
        return ref

    def _register_capsule(self, ref, capsule, type_ref, t, piece):
        self._ref_to_rec[ref] = self._Rec(capsule, type_ref, t, piece)
        self._piece_to_ref[piece] = ref

    def put(self, piece, t=None):
        try:
            return self._piece_to_ref[piece]
        except TypeError as x:
            raise RuntimeError(f"{x}: {piece}")
        except KeyError:
            pass
        t = t or deduce_value_type(piece)
        log.debug('Registering piece %r: %s', t.name, piece)
        capsule = make_capsule(self, self._pyobj_creg, piece, t)
        ref = make_ref(capsule)
        self._register_capsule(ref, capsule, capsule.type_ref, t, piece)
        log.debug('Registered piece %s (type: %s): %r', ref, capsule.type_ref, piece)
        return ref

    def add_to_cache(self, piece, t, ref):
        self._ref_to_rec[ref] = self._Rec(None, None, t, piece)
        self._piece_to_ref[piece] = ref

    def put_opt(self, piece, t=None):
        if piece is None:
            return None
        return self.put(piece, t)

    def get(self, ref):
        rec = self._ref_to_rec.get(ref)
        if rec:
            return rec.capsule
        else:
            return None

    # Alias for web source.
    def pull(self, ref):
        return self.get(ref)

    def resolve_ref(self, ref, expected_type=None):
        try:
            return self._ref_to_rec[ref]
        except KeyError:
            raise KeyError(f"Unknown ref: {ref}")
