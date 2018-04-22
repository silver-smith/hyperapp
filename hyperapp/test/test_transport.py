
from pathlib import Path
import pytest

from hyperapp.common.identity import Identity
from hyperapp.common.module_registry import ModuleRegistry
from hyperapp.common.services import ServicesBase
from hyperapp.common.module_manager import ModuleManager
from hyperapp.common import dict_coders, cdr_coders  # self-registering


class PhonyModuleRegistry(ModuleRegistry):

    def register(self, module):
        pass


class Services(ServicesBase):

    def __init__(self):
        self.interface_dir = Path(__file__).parent.joinpath('../common/interface').resolve()
        self.hyperapp_dir = Path(__file__).parent.parent.resolve()
        ServicesBase.init_services(self)
        self._load_type_modules([
            'module',
            'error',
            'hyper_ref',
            'phony_transport',
            'encrypted_transport',
            ])
        self.module_registry = PhonyModuleRegistry()
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.module_registry)
        self.module_manager.register_meta_hook()
        for module_name in [
                'common.ref_registry',
                ]:
            self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)

            

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
