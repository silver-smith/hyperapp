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


class RefAndAssSet:

    def __init__(self):
        self.refs = set()
        self.asss = set()

    def __or__(self, rhs):
        result = RefAndAssSet()
        result.refs |= self.refs
        result.refs |= rhs.refs
        result.asss |= self.asss
        result.asss |= rhs.asss
        return result


class Bundler:

    def __init__(self):
        pass

    def bundle(self, ref_list, seen_refs=None):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.debug('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        refass, capsule_list = self._collect_capsule_list(ref_list, seen_refs or [])
        bundle = bundle_t(
            roots=ref_list,
            associations=list(refass.asss),
            capsule_list=capsule_list,
            )
        return _RefsAndBundle(refass.refs, bundle)

    def _collect_capsule_list(self, ref_list, seen_refs):
        result = RefAndAssSet()
        type_ref_set = set()
        ref_to_capsule = {}
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
                ref_to_capsule[ref] = capsule
                type_ref_set.add(capsule.type_ref)
                new_ref_set.add(capsule.type_ref)
                collected = self._collect_refs_from_capsule(ref, capsule)
                new_ref_set |= collected.refs
                result.asss |= collected.asss
                processed_ref_set.add(ref)
            ref_set = new_ref_set - processed_ref_set
            if not ref_set:
                break
        else:
            raise RuntimeError(f"Reached recursion limit {RECURSION_LIMIT} while resolving refs")
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        result.refs = processed_ref_set
        # Types should come first, or unbundler won't be able to decode capsules.
        type_capsules = [
            capsule for ref, capsule
            in ref_to_capsule.items()
            if ref in type_ref_set
            ]
        other_capsules = [
            capsule for ref, capsule
            in ref_to_capsule.items()
            if ref not in type_ref_set
            ]
        return (result, type_capsules + other_capsules)

    def _collect_refs_from_capsule(self, ref, capsule):
        dc = decode_capsule(types, capsule)
        log.debug('Collecting refs from %r:', dc.value)
        result = RefAndAssSet()
        result.refs |= pick_refs(dc.t, dc.value)
        result |= self._collect_associations(ref, dc.t, dc.value)
        log.debug('Collected %d refs from %s %s: %s', len(result.refs), dc.t, ref,
                 ', '.join(map(ref_repr, result.refs)))
        return result

    def _collect_associations(self, ref, t, value):
        result = RefAndAssSet()
        t_res = pyobj_creg.reverse_resolve(t)
        for obj in [t_res, value]:
            for ass in association_reg.base_to_ass_list(obj):
                piece = ass.to_piece(mosaic)
                ass_ref = mosaic.put(piece)
                log.debug("Bundle association %s: %s (%s)", ass_ref, ass, piece)
                result.asss.add(ass_ref)
                result.refs.add(ass_ref)  # Should collect from these refs too.
        return result


@mark.service
def bundler():
    def _bundle(ref_list, seen_refs=None):
        return Bundler().bundle(ref_list, seen_refs)
    return _bundle
