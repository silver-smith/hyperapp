from collections import namedtuple
from datetime import datetime
import logging

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.util import is_list_inst
from hyperapp.common.ref import decode_capsule, ref_repr
from hyperapp.common.module import Module

from .services import (
    association_reg,
    mark,
    mosaic,
    pick_refs,
    pyobj_creg,
    types,
    )

log = logging.getLogger(__name__)


RECURSION_LIMIT = 100

_RefsAndBundle = namedtuple('_RefsAndBundle', 'ref_set bundle')


class Bundler:

    def __init__(self):
        self._collected_ass_set = set()

    def bundle(self, ref_list, seen_refs=None):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.debug('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        ref_set, capsule_list = self._collect_capsule_list(ref_list, seen_refs or [])
        bundle = bundle_t(
            roots=ref_list,
            associations=list(self._collected_ass_set),
            capsule_list=capsule_list,
            )
        return _RefsAndBundle(ref_set, bundle)

    def _collect_capsule_list(self, ref_list, seen_refs):
        collected_type_ref_set = set()
        capsule_set = set()
        type_capsule_set = set()
        missing_ref_count = 0
        processed_ref_set = set(seen_refs)
        ref_set = set(ref_list)
        for i in range(RECURSION_LIMIT):
            new_ref_set = set()
            for ref in ref_set:
                if ref.hash_algorithm == 'phony':
                    continue
                capsule = mosaic.get(ref)
                if capsule is None:
                    log.warning('Ref %s is failed to be resolved', ref_repr(ref))
                    missing_ref_count += 1
                    continue
                if ref in collected_type_ref_set:
                    type_capsule_set.add(capsule)
                else:
                    capsule_set.add(capsule)
                collected_type_ref_set.add(capsule.type_ref)
                new_ref_set.add(capsule.type_ref)
                new_ref_set |= self._collect_refs_from_capsule(ref, capsule)
                processed_ref_set.add(ref)
            ref_set = new_ref_set - processed_ref_set
            if not ref_set:
                break
        else:
            raise RuntimeError(f"Reached recursion limit {RECURSION_LIMIT} while resolving refs")
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        # types should come first, or receiver won't be able to decode
        return (processed_ref_set, list(type_capsule_set) + list(capsule_set))

    def _collect_refs_from_capsule(self, ref, capsule):
        dc = decode_capsule(types, capsule)
        log.debug('Collecting refs from %r:', dc.value)
        ref_set = set()
        ref_set |= pick_refs(dc.t, dc.value)
        ref_set |= self._collect_associations(ref, dc.t, dc.value)
        log.debug('Collected %d refs from %s %s: %s', len(ref_set), dc.t, ref,
                 ', '.join(map(ref_repr, ref_set)))
        return ref_set

    def _collect_associations(self, ref, t, value):
        ref_set = set()
        t_res = pyobj_creg.reverse_resolve(t)
        for obj in [t_res, value]:
            for ass in association_reg.base_to_ass_list(obj):
                piece = ass.to_piece(mosaic)
                ass_ref = mosaic.put(piece)
                log.debug("Bundle association %s: %s (%s)", ass_ref, ass, piece)
                self._collected_ass_set.add(ass_ref)
                ref_set.add(ass_ref)  # Should collect from these refs too.
        return ref_set


@mark.service
def bundler():
    def _bundle(ref_list, seen_refs=None):
        return Bundler().bundle(ref_list, seen_refs)
    return _bundle
