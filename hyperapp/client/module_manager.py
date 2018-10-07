import logging
from ..common import module_manager as common_module_manager
from .registry import DynamicModuleRegistryProxy

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__(self, services):
        super().__init__(services, services.types, services.module_registry)
        self._id2module = {}

    def load_code_module(self, module, fullname=None):
        common_module_manager.ModuleManager.load_code_module(self, module)
        self._id2module[module.id] = module

    def resolve_ids(self, module_ids):
        modules = []
        for id in module_ids:
            if id in self._types: continue  # do not return type modules
            module = self._id2module[id]
            modules.append(module)
        return modules
