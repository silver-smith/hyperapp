from hyperapp.common.module_registry import ModuleRegistry
from hyperapp.common.module_manager import ModuleManager
from hyperapp.server.services import ServerServicesBase
from hyperapp.server.module import ServerModule
from hyperapp.client.services import ClientServicesBase


class PhonyModuleRegistry(ModuleRegistry):

    def __init__(self):
        self._module_list = []

    def register(self, module):
        self._module_list.append(module)  # preserves import order

    def init_phases(self, services):
        for module in self._module_list:
            if isinstance(module, ServerModule):
                module.init_phase2(services)
        for module in self._module_list:
            if isinstance(module, ServerModule):
                module.init_phase3(services)


class TestServicesMixin(object):

    __test__ = False

    def init_module_manager(self):
        self.module_registry = PhonyModuleRegistry()
        self.module_manager = ModuleManager(self, self.types, self.module_registry)

    def load_modules(self, type_module_list, code_module_list):
        self.module_manager.register_meta_hook()
        try:
            self._load_type_modules(type_module_list)
            for module_name in code_module_list:
                self.module_manager.load_code_module_by_name(self.types, self.hyperapp_dir, module_name)
        finally:
            self.module_manager.unregister_meta_hook()


class TestServerServices(ServerServicesBase, TestServicesMixin):

    def __init__(self, type_module_list, code_module_list, config=None):
        super().__init__()
        self.init_services(config)
        self.init_module_manager()
        self.load_modules(type_module_list, code_module_list)
        self.module_registry.init_phases(self)


class TestClientServices(ClientServicesBase, TestServicesMixin):

    def __init__(self, event_loop, type_module_list, code_module_list):
        super().__init__()
        self.event_loop = event_loop
        self.init_services()
        self.init_module_manager()
        self.load_modules(type_module_list, code_module_list)
