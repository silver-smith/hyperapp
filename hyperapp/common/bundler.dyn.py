from collections import namedtuple
from datetime import datetime
import logging

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.htypes.association import association_t
from hyperapp.common.util import is_list_inst
from hyperapp.common.ref import decode_capsule, ref_repr
from hyperapp.common.module import Module

from .services import (
    association_reg,
    mark,
    mosaic,
    python_object_creg,
    types,
    )
from .code.visitor import Visitor

log = logging.getLogger(__name__)


RECURSION_LIMIT = 100

_RefsAndBundle = namedtuple('_RefsAndBundle', 'ref_set bundle')

_aux_bundler_hooks = []


class Bundler(Visitor):

    def __init__(self):
        self._collected_ref_set = None
        self._collected_type_ref_set = None
        self._collected_aux_set = set()

    def bundle(self, ref_list, seen_refs=None):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.debug('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        ref_set, capsule_list = self._collect_capsule_list(ref_list, seen_refs or [])
        bundle = bundle_t(
            roots=ref_list,
            aux_roots=list(self._collected_aux_set),
            capsule_list=capsule_list,
            )
        return _RefsAndBundle(ref_set, bundle)

    def _collect_capsule_list(self, ref_list, seen_refs):
        self._collected_type_ref_set = set()
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
                if ref in self._collected_type_ref_set:
                    type_capsule_set.add(capsule)
                else:
                    capsule_set.add(capsule)
                self._collected_type_ref_set.add(capsule.type_ref)
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
        self._collected_ref_set = set()
        self._collect_refs_from_object(dc.t, dc.value)
        self._collect_aux_refs(ref, dc.t, dc.value)
        log.debug('Collected %d refs from %s %s: %s', len(self._collected_ref_set), dc.t, ref,
                 ', '.join(map(ref_repr, self._collected_ref_set)))
        return self._collected_ref_set

    def _collect_refs_from_object(self, t, object):
        self.visit(t, object)

    def visit_record(self, t, value):
        if t == ref_t:
            self._collected_ref_set.add(value)

    def _collect_aux_refs(self, ref, t, value):
        for obj in [t, value]:
            for ass in association_reg.base_to_ass_list(obj):
                piece = self._ass_to_piece(ass)
                ass_ref = mosaic.put(piece)
                log.debug("Bundle aux association %s: %s (%s)", ass_ref, ass, piece)
                self._collected_aux_set.add(ass_ref)
                self._collected_ref_set.add(ass_ref)  # Should collect from these refs too.
        for hook in _aux_bundler_hooks:
            aux_ref_set = set(hook(ref, t, value) or [])
            if aux_ref_set:
                log.debug("Bundle aux by hook %s %s %s: %s", hook, t, value, aux_ref_set)
                self._collected_aux_set |= aux_ref_set
                self._collected_ref_set |= aux_ref_set  # Should collect from these refs too.

    @staticmethod
    def _ass_to_piece(ass):
        def obj_to_ref(obj):
            return mosaic.put(
                python_object_creg.reverse_resolve(obj)
            )

        if isinstance(ass.key, tuple):
            key = ass.key
        else:
            key = [ass.key]
        return association_t(
            bases=[obj_to_ref(obj) for obj in ass.bases],
            key=[mosaic.put(piece) for piece in key],
            value=mosaic.put(ass.value),
            )


@mark.service
def aux_bundler_hooks():
    return _aux_bundler_hooks


@mark.service
def bundler():
    def _bundle(ref_list, seen_refs=None):
        return Bundler().bundle(ref_list, seen_refs)
    return _bundle
