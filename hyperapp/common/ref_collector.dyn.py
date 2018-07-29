import logging

from .util import is_list_inst, full_type_name_to_str
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

    def __init__(self, types, ref_resolver, route_resolver):
        super().__init__(error_types, packet_types, core_types)
        self._types = types
        self._ref_resolver = ref_resolver
        self._route_resolver = route_resolver
        self._collected_ref_set = None
        self._collected_route_set = set()

    def make_bundle(self, ref_list):
        assert is_list_inst(ref_list, href_types.ref), repr(ref_list)
        capsule_list = self._collect_capsule_list(ref_list)
        return href_types.bundle(
            roots=ref_list,
            capsule_list=capsule_list,
            route_list=list(self._collected_route_set),
            )

    def _collect_capsule_list(self, ref_list):
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
                new_ref_set |= self._collect_refs(ref, capsule)
            if not new_ref_set:
                break
            ref_set = new_ref_set
        else:
            assert False, 'Reached recursion limit %d while resolving refs' % RECURSION_LIMIT
        if missing_ref_count:
            log.warning('Failed to resolve %d refs', missing_ref_count)
        return list(capsule_set)

    def _collect_refs(self, ref, capsule):
        t = self._types.resolve(capsule.full_type_name)
        object = decode_object(t, capsule)
        log.info('Collecting refs from %r:', object)
        self._collected_ref_set = set()
        self.visit(t, object)
        if full_type_name_to_str(t.full_name) in ['hyper_ref.endpoint', 'hyper_ref.service']:
            transport_ref_set = self._handle_endpoint_ref(ref)
            self._collected_ref_set |= transport_ref_set
        log.debug('Collected %d refs from %s %s: %s',
                      len(self._collected_ref_set), full_type_name_to_str(t.full_name), object, ', '.join(map(ref_repr, self._collected_ref_set)))
        return self._collected_ref_set

    def visit_primitive(self, t, value):
        if t == href_types.ref:
            self._collected_ref_set.add(value)

    def _handle_endpoint_ref(self, endpoint_ref):
        transport_ref_set = self._route_resolver.resolve(endpoint_ref)
        for transport_ref in transport_ref_set:
            self._collected_route_set.add(href_types.route(
                endpoint_ref=endpoint_ref,
                transport_ref=transport_ref,
                ))
        return transport_ref_set


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._types = services.types
        self._ref_resolver = services.ref_resolver
        self._route_resolver = services.route_resolver
        services.ref_collector_factory = self._ref_collector_factory

    def _ref_collector_factory(self):
        return RefCollector(self._types, self._ref_resolver, self._route_resolver)
