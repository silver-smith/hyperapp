# reference registry: map refs to capsules

import logging
import threading
from collections import namedtuple

from .htypes import capsule_t
from .htypes.deduce_value_type import deduce_value_type_with_list
from .ref import DecodedCapsule, decode_capsule, make_capsule, make_ref
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Mosaic:

    _Rec = namedtuple('_Rec', 'capsule type_ref t value')

    def __init__(self, pyobj_creg):
        self._pyobj_creg = pyobj_creg
        self._ref_to_rec = {}  # ref -> _Rec
        self._piece_to_ref = {}
        self._lock = threading.Lock()

    def register_capsule(self, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule of type %s', ref, capsule.type_ref)
        with self._lock:
            rec = self._ref_to_rec.get(ref)
            if rec:
                log.debug('  (already exists)')
                assert capsule == rec.capsule, repr((rec.capsule, capsule))  # new capsule does not match existing one
                return
            dc = decode_capsule(self._pyobj_creg, capsule)
            self._register_capsule(dc.value, dc.t, ref, dc.type_ref, capsule)
            return ref

    def put(self, piece, t=None):
        try:
            return self._piece_to_ref[piece, type(piece)]
        except TypeError as x:
            raise RuntimeError(f"{x}: {piece}")
        except KeyError:
            pass
        t = t or deduce_value_type_with_list(self._pyobj_creg, piece)
        # make_capsule should be outside the lock as mosaic.put is called somewhere inside it.
        capsule = make_capsule(self._pyobj_creg, piece, t)
        ref = make_ref(capsule)
        with self._lock:
            try:
                # Check it is not added by another thread.
                return self._piece_to_ref[piece, type(piece)]
            except KeyError:
                pass
            log.debug('Registering piece %r: %s', t.name, piece)
            self._register_capsule(piece, t, ref, capsule.type_ref, capsule)
            log.debug('Registered piece %s (type: %s): %r', ref, capsule.type_ref, piece)
            return ref

    def _register_capsule(self, piece, t, ref, type_ref, capsule):
        self._ref_to_rec[ref] = self._Rec(capsule, type_ref, t, piece)
        self._piece_to_ref[piece, type(piece)] = ref

    def add_to_cache(self, piece, t, ref):
        with self._lock:
            self._register_capsule(piece, t, ref, None, None)

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
