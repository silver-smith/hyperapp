
from pathlib import Path
import pytest

from hyperapp.common.identity import Identity
from hyperapp.common.module_registry import ModuleRegistry
from hyperapp.common.services import ServicesBase
from hyperapp.common.module_manager import ModuleManager
from hyperapp.common import dict_coders, cdr_coders  # self-registering


HYPERAPP_DIR = Path(__file__).parent.parent.resolve()


type_module_list = [
    'module',
    'error',
    'hyper_ref',
    'phony_transport',
    'encrypted_transport',
    ]

code_module_list = [
    'common.ref_registry',
    'server.ref_resolver',
    ]


class PhonyModuleRegistry(ModuleRegistry):

    def register(self, module):
        pass


class Services(ServicesBase):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR
        self.interface_dir = HYPERAPP_DIR / 'common' / 'interface'
        ServicesBase.init_services(self)
        self._load_type_modules(type_module_list)
        self.module_registry = PhonyModuleRegistry()
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.module_registry)
        self.module_manager.register_meta_hook()
        try:
            for module_name in code_module_list:
                self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
        except:
            self.module_manager.unregister_meta_hook()
            raise

            

@pytest.fixture
def services():
    return Services()


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
    

def test_services_should_load(services, transport_ref):
    pass
