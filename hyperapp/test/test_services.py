from hyperapp.common.module_registry import ModuleRegistry
from hyperapp.common.module_manager import ModuleManager
from hyperapp.common.services import ServicesBase


class PhonyModuleRegistry(ModuleRegistry):

    def register(self, module):
        pass


class TestServices(ServicesBase):

    __test__ = False

    def __init__(self, type_module_list, code_module_list, config=None):
        super().__init__()
        self.on_start = []
        self.on_stop = []
        ServicesBase.init_services(self, config)
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
