
from pathlib import Path
import pytest

from hyperapp.common.identity import Identity
from hyperapp.common.module_registry import ModuleRegistry
from hyperapp.common.services import ServicesBase
from hyperapp.common.module_manager import ModuleManager
from hyperapp.common import dict_coders, cdr_coders  # self-registering


HYPERAPP_DIR = Path(__file__).parent.parent.resolve()
REF_RESOLVER_SERVICE_ID = 'ref_resolver'  # todo: copy-paste from server.server_ref_resolver


type_module_list = [
    'error',
    'resource',
    'core',
    'hyper_ref',
    'module',
    'packet',
    'phony_transport',
    'tcp_transport',
    'encrypted_transport',
    ]

code_module_list = [
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'server.transport.tcp',
    'server.transport.encrypted',
    'client.async_ref_resolver',
    ]


class PhonyModuleRegistry(ModuleRegistry):

    def register(self, module):
        pass


class Services(ServicesBase):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR
        self.interface_dir = HYPERAPP_DIR / 'common' / 'interface'
        ServicesBase.init_services(self)
        self.module_registry = PhonyModuleRegistry()
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.module_registry)
        self.module_manager.register_meta_hook()
        try:
            self._load_type_modules(type_module_list)
            for module_name in code_module_list:
                self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
        except:
            self.close()
            raise

    def close(self):
        self.module_manager.unregister_meta_hook()


@pytest.fixture
def services():
    services = Services()
    yield services
    services.close()


@pytest.fixture
def transport_ref(services):
    types = services.types
    phony_transport_route = types.phony_transport.route()
    phony_transport_ref = services.ref_registry.register_object(types.phony_transport.route, phony_transport_route)
    identity = Identity.generate(fast=True)
    encrypted_transport_route = types.encrypted_transport.route(
        public_key_der=identity.public_key.to_der(),
        base_transport_ref=phony_transport_ref)
    encrypted_transport_ref = services.ref_registry.register_object(types.encrypted_transport.route, encrypted_transport_route)
    return encrypted_transport_ref

@pytest.fixture
def ref_resolver_parcel(services, transport_ref):
    href_types = services.types.hyper_ref
    service_ref = href_types.service_ref(['hyper_ref', 'ref_resolver'], REF_RESOLVER_SERVICE_ID, transport_ref)
    ref_resolver_ref = services.ref_registry.register_object(href_types.service_ref, service_ref)
    ref_collector = services.ref_collector_factory()
    referred_list = ref_collector.collect_referred(ref_resolver_ref)
    return href_types.parcel(ref_resolver_ref, referred_list)

def test_services_should_load(services, ref_resolver_parcel):
    pass
