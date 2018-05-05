import logging

from .interface import error as error_types
from .interface import packet as packet_types
from .interface import core as core_types
from .interface import hyper_ref as href_types
from .ref import ref_repr, decode_object
from .visitor import Visitor
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_collector'
RECURSION_LIMIT = 100


class RefCollector(Visitor):

    def __init__(self, type_registry_registry, ref_resolver):
        super().__init__(error_types, packet_types, core_types)
        self._type_registry_registry = type_registry_registry
        self._ref_resolver = ref_resolver
        self._collected_ref_set = None

    def make_bundle(self, ref):
        referred_list = self.collect_referred(ref)
        return href_types.bundle(ref, referred_list)

    def collect_referred(self, ref):
        referred_set = set()
        missing_ref_count = 0
        ref_set = set([ref])
        for i in range(RECURSION_LIMIT):
            new_ref_set = set()
            for ref in ref_set:
                referred = self._ref_resolver.resolve_ref(ref)
                if not referred:
                    missing_ref_count += 1
                    continue
                referred_set.add(referred)
                new_ref_set |= self._collect_refs(referred)
            if not new_ref_set:
                break
            ref_set = new_ref_set
        else:
            assert False, 'Reached recursion limit %d while resolving refs' % RECURSION_LIMIT
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        return list(referred_set)

    def _collect_refs(self, referred):
        t = self._type_registry_registry.resolve_type(referred.full_type_name)
        object = decode_object(t, referred)
        self._collected_ref_set = set()
        self.visit(t, object)
        log.debug('Collected %d refs from %s %s: %s',
                      len(self._collected_ref_set), '.'.join(t.full_name), object, ', '.join(map(ref_repr, self._collected_ref_set)))
        return self._collected_ref_set

    def visit_primitive(self, t, value):
        if t == href_types.ref:
            self._collected_ref_set.add(value)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._type_registry_registry = services.type_registry_registry
        self._ref_resolver = services.ref_resolver
        services.ref_collector_factory = self._ref_collector_factory

    def _ref_collector_factory(self):
        return RefCollector(self._type_registry_registry, self._ref_resolver)
