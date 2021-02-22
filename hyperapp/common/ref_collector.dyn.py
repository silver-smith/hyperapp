from datetime import datetime
import logging

from dateutil.tz import tzlocal

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.util import is_list_inst
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module

from .visitor import Visitor

log = logging.getLogger(__name__)

RECURSION_LIMIT = 100


class RefCollector(Visitor):

    def __init__(self, mosaic, types, aux_ref_collector_hooks):
        self._mosaic = mosaic
        self._types = types
        self._aux_ref_collector_hooks = aux_ref_collector_hooks
        self._collected_ref_set = None
        self._collected_type_ref_set = None
        self._collected_aux_set = set()

    def make_bundle(self, ref_list):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.info('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        capsule_list = self._collect_capsule_list(ref_list)
        return bundle_t(
            roots=ref_list,
            aux_roots=list(self._collected_aux_set),
            capsule_list=capsule_list,
            )

    def _collect_capsule_list(self, ref_list):
        self._collected_type_ref_set = set()
        capsule_set = set()
        type_capsule_set = set()
        missing_ref_count = 0
        ref_set = set(ref_list)
        for i in range(RECURSION_LIMIT):
            new_ref_set = set()
            for ref in ref_set:
                if ref.hash_algorithm == 'phony':
                    continue
                capsule = self._mosaic.get(ref)
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
            if not new_ref_set:
                break
            ref_set = new_ref_set
        else:
            raise RuntimeError(f"Reached recursion limit {RECURSION_LIMIT} while resolving refs")
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        # types should come first, or receiver won't be able to decode
        return list(type_capsule_set) + list(capsule_set)

    def _collect_refs_from_capsule(self, ref, capsule):
        t = self._types.resolve(capsule.type_ref)
        object = self._types.decode_object(t, capsule)
        log.debug('Collecting refs from %r:', object)
        self._collected_ref_set = set()
        self._collect_refs_from_object(t, object)
        self._collect_aux_refs(ref, t, object)
        log.debug('Collected %d refs from %s %s: %s', len(self._collected_ref_set), t, ref_repr(ref),
                 ', '.join(map(ref_repr, self._collected_ref_set)))
        return self._collected_ref_set

    def _collect_refs_from_object(self, t, object):
        self.visit(t, object)

    def visit_record(self, t, value):
        if t == ref_t:
            self._collected_ref_set.add(value)

    def _collect_aux_refs(self, ref, t, object):
        for hook in self._aux_ref_collector_hooks:
            self._collected_aux_set |= set(hook(ref, t, object) or [])


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._mosaic = services.mosaic
        self._types = services.types
        self._aux_ref_collector_hooks = []
        services.aux_ref_collector_hooks = self._aux_ref_collector_hooks
        services.ref_collector_factory = self.ref_collector_factory

    def ref_collector_factory(self):
        return RefCollector(self._mosaic, self._types, self._aux_ref_collector_hooks)
