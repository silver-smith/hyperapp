
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
    'test',
    ]

server_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'server.transport.registry',
    'server.transport.tcp',
    'server.transport.encrypted',
    'server.remoting',
    ]

client_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'client.async_ref_resolver',
    'client.piece_registry',
    'client.transport.registry',
    'client.transport.phony',
    'client.remoting_proxy',
    ]


class PhonyModuleRegistry(ModuleRegistry):

    def register(self, module):
        pass


class Services(ServicesBase):

    def __init__(self, code_module_list):
        self.hyperapp_dir = HYPERAPP_DIR
        self.interface_dir = HYPERAPP_DIR / 'common' / 'interface'
        ServicesBase.init_services(self)
        self.module_registry = PhonyModuleRegistry()
        self.module_manager = ModuleManager(self, self.types, self.module_registry)
        self.module_manager.register_meta_hook()
        try:
            self._load_type_modules(type_module_list)
            for module_name in code_module_list:
                self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
        finally:
            self.module_manager.unregister_meta_hook()

    def close(self):
        pass


@pytest.fixture
def client_services():
    services = Services(client_code_module_list)
    yield services
    services.close()

@pytest.fixture
def server_services():
    services = Services(server_code_module_list)
    yield services
    services.close()


@pytest.fixture
def transport_ref(server_services):
    types = server_services.types
    phony_transport_address = types.phony_transport.address()
    phony_transport_ref = server_services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)
    identity = Identity.generate(fast=True)
    encrypted_transport_address = types.encrypted_transport.address(
        public_key_der=identity.public_key.to_der(),
        base_transport_ref=phony_transport_ref)
    encrypted_transport_ref = server_services.ref_registry.register_object(types.encrypted_transport.address, encrypted_transport_address)
    #return encrypted_transport_ref
    return phony_transport_ref

@pytest.fixture
def ref_resolver_bundle(server_services, transport_ref):
    href_types = server_services.types.hyper_ref
    service_ref = href_types.service_ref(['test', 'echo'], REF_RESOLVER_SERVICE_ID, transport_ref)
    ref_resolver_ref = server_services.ref_registry.register_object(href_types.service_ref, service_ref)
    ref_collector = server_services.ref_collector_factory()
    piece_list = ref_collector.collect_piece(ref_resolver_ref)
    return href_types.bundle(ref_resolver_ref, piece_list)

@pytest.mark.asyncio
async def test_services_should_load(client_services, server_services, ref_resolver_bundle):
    client_services.ref_registry.register_bundle(ref_resolver_bundle)
    proxy = await client_services.proxy_factory.from_ref(ref_resolver_bundle.ref)
    await proxy.say('hello')
    request_bundle = client_services.phony_transport_bundle_list.pop(client_services.types.hyper_ref.bundle)
    server_services.ref_registry.register_bundle(request_bundle)
    server_services.transport_resolver.resolve(request_bundle.ref)
