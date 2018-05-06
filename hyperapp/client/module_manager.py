import logging
from ..common import module_manager as common_module_manager
from .registry import DynamicModuleRegistryProxy

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__(self, services):
        super().__init__(services, services.types, services.module_registry)
        self._id2module = {}

    def init_types(self, services):
        self._objimpl_registry = services.objimpl_registry
        self._view_registry = services.view_registry
        self._param_editor_registry = services.param_editor_registry

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

    def _register_provided_services(self, module, module_dict):
        common_module_manager.ModuleManager._register_provided_services(self, module, module_dict)

        def register(fn_name, registry):
            fn = module_dict.get(fn_name)
            if fn:
                log.debug('ModuleManager: module %s: registering %s...', module.id, fn_name)
                fn(DynamicModuleRegistryProxy(registry, module.id), self._services)

        register('register_object_implementations', self._objimpl_registry)
        register('register_views', self._view_registry)
        register('register_param_editors', self._param_editor_registry)
