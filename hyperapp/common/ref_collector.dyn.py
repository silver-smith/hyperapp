from collections import namedtuple
from datetime import datetime
import logging

from dateutil.tz import tzlocal

from hyperapp.common.htypes import ref_t, bundle_t
from hyperapp.common.util import is_list_inst
from hyperapp.common.ref import decode_capsule, ref_repr
from hyperapp.common.module import Module

from .visitor import Visitor

log = logging.getLogger(__name__)

RECURSION_LIMIT = 100


_RefsAndBundle = namedtuple('_RefsAndBundle', 'ref_set bundle')


class RefCollector(Visitor):

    def __init__(self, mosaic, types, aux_ref_collector_hooks):
        self._mosaic = mosaic
        self._types = types
        self._aux_ref_collector_hooks = aux_ref_collector_hooks
        self._collected_ref_set = None
        self._collected_type_ref_set = None
        self._collected_aux_set = set()

    def collect(self, ref_list):
        assert is_list_inst(ref_list, ref_t), repr(ref_list)
        log.info('Making bundle from refs: %s', [ref_repr(ref) for ref in ref_list])
        ref_set, capsule_list = self._collect_capsule_list(ref_list)
        bundle = bundle_t(
            roots=ref_list,
            aux_roots=list(self._collected_aux_set),
            capsule_list=capsule_list,
            )
        return _RefsAndBundle(ref_set, bundle)

    def _collect_capsule_list(self, ref_list):
        self._collected_type_ref_set = set()
        capsule_set = set()
        type_capsule_set = set()
        missing_ref_count = 0
        processed_ref_set = set()
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
        dc = decode_capsule(self._types, capsule)
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

    def _collect_aux_refs(self, ref, t, object):
        for hook in self._aux_ref_collector_hooks:
            aux_ref_set = set(hook(ref, t, object) or [])
            self._collected_aux_set |= aux_ref_set
            self._collected_ref_set |= aux_ref_set  # Should collect these refs too.


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        self._types = services.types
        self._aux_ref_collector_hooks = []
        services.aux_ref_collector_hooks = self._aux_ref_collector_hooks
        services.ref_collector = self.ref_collector

    def ref_collector(self, ref_list):
        collector = RefCollector(self._mosaic, self._types, self._aux_ref_collector_hooks)
        return collector.collect(ref_list)
