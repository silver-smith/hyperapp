from collections import defaultdict, namedtuple
from datetime import datetime
import logging

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.util import is_list_inst
from hyperapp.common.ref import ref_repr

from .services import (
    association_reg,
    mark,
    mosaic,
    pick_refs,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


RECURSION_LIMIT = 100

_RefsAndBundle = namedtuple('_RefsAndBundle', 'ref_set bundle')


class RefAndAssSet:

    def __init__(self, refs=None, asss=None):
        self.refs = refs or set()
        self.asss = asss or set()

    def __or__(self, rhs):
        return RefAndAssSet(
            refs=self.refs | rhs.refs,
            asss=self.asss | rhs.asss,
            )


def _sort_deps(ref_set, dep_set):
    result = []
    visited = set()

    def visit(ref):
        if ref in visited:
            return
        for dep in dep_set[ref]:
            visit(dep)
        result.append(ref)
        visited.add(ref)

    for ref in ref_set:
        visit(ref)

    return result


class Bundler:

    def __init__(self):
        pass

    def bundle(self, ref_list, seen_refs=None):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.debug('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        refass, capsule_list = self._collect_capsule_list(ref_list, seen_refs or [])
        bundle = bundle_t(
            roots=tuple(ref_list),
            associations=tuple(refass.asss),
            capsule_list=tuple(capsule_list),
            )
        return _RefsAndBundle(refass.refs, bundle)

    def _collect_capsule_list(self, ref_list, seen_refs):
        result = RefAndAssSet()
        ref_to_capsule = {}
        deps = defaultdict(set)
        missing_ref_count = 0
        processed_ref_set = set(seen_refs)
        ref_set = set(ref_list)
        for i in range(RECURSION_LIMIT):
            new_ref_set = set()
            for ref in ref_set:
                if ref.hash_algorithm == 'phony':
                    continue
                rec = mosaic.resolve_ref(ref)
                if rec is None:
                    log.warning('Ref %s is failed to be resolved', ref_repr(ref))
                    missing_ref_count += 1
                    continue
                ref_to_capsule[ref] = rec.capsule
                new_ref_set.add(rec.type_ref)
                collected = self._collect_refs_from_capsule(ref, rec)
                new_ref_set |= collected.refs | collected.asss
                result.asss |= collected.asss
                deps[ref] |= collected.refs | {rec.type_ref}
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
        sorted_refs = _sort_deps(ref_to_capsule, deps)
        capsules = [
            ref_to_capsule[ref]
            for ref in sorted_refs
            if ref in ref_to_capsule
            ]
        return (result, capsules)

    def _collect_refs_from_capsule(self, ref, rec):
        log.debug('Collecting refs from %r:', rec.value)
        refs = pick_refs(rec.t, rec.value)
        asss = self._collect_associations(ref, rec.t, rec.value)
        log.debug('Collected %d refs from %s %s: %s', len(refs), rec.t, ref,
                 ', '.join(map(ref_repr, refs)))
        return RefAndAssSet(refs, asss)

    def _collect_associations(self, ref, t, value):
        result = set()
        t_res = pyobj_creg.actor_to_piece(t)
        for obj in [t_res, value]:
            for ass in association_reg.base_to_ass_list(obj):
                piece = ass.to_piece(mosaic)
                ass_ref = mosaic.put(piece)
                log.debug("Bundle association %s: %s (%s)", ass_ref, ass, piece)
                result.add(ass_ref)
        return result


@mark.service
def bundler():
    def _bundle(ref_list, seen_refs=None):
        return Bundler().bundle(ref_list, seen_refs)
    return _bundle
