import logging

from .util import is_list_inst
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

    def __init__(self, types, ref_resolver):
        super().__init__(error_types, packet_types, core_types)
        self._types = types
        self._ref_resolver = ref_resolver
        self._collected_ref_set = None

    def make_bundle(self, ref_list):
        assert is_list_inst(ref_list, href_types.ref), repr(ref_list)
        capsule_list = self.collect_capsule(ref_list)
        return href_types.bundle(ref_list, capsule_list)

    def collect_capsule(self, ref_list):
        capsule_set = set()
        missing_ref_count = 0
        ref_set = set(ref_list)
        for i in range(RECURSION_LIMIT):
            new_ref_set = set()
            for ref in ref_set:
                capsule = self._ref_resolver.resolve_ref(ref)
                if not capsule:
                    missing_ref_count += 1
                    continue
                capsule_set.add(capsule)
                new_ref_set |= self._collect_refs(capsule)
            if not new_ref_set:
                break
            ref_set = new_ref_set
        else:
            assert False, 'Reached recursion limit %d while resolving refs' % RECURSION_LIMIT
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        return list(capsule_set)

    def _collect_refs(self, capsule):
        t = self._types.resolve(capsule.full_type_name)
        object = decode_object(t, capsule)
        log.info('Collecting refs from %r:', object)
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
        self._types = services.types
        self._ref_resolver = services.ref_resolver
        services.ref_collector_factory = self._ref_collector_factory

    def _ref_collector_factory(self):
        return RefCollector(self._types, self._ref_resolver)
