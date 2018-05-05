import logging

from hyperapp.common.interface import phony_transport as phony_transport_types
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.phony'


class Transport(object):

    def __init__(self, ref_collector_factory, bundle_list):
        self._ref_collector_factory = ref_collector_factory
        self._bundle_list = bundle_list

    def send(self, ref):
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle(ref)
        self._bundle_list.put(bundle)


class BundleList(object):

    def __init__(self):
        self._bundle_list = []

    def put(self, bundle):
        self._bundle_list.append(bundle)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.phony_transport_bundle_list = bundle_list = BundleList()
        services.transport_registry.register(phony_transport_types.address, self._resolve_address, services.ref_collector_factory, bundle_list)

    def _resolve_address(self, address, ref_collector_factory, bundle_list):
        return Transport(ref_collector_factory, bundle_list)
