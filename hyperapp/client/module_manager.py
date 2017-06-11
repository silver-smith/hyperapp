import logging
from ..common.htypes import (
    builtin_type_registry,
    )
from ..common import module_manager as common_module_manager
from .registry import DynamicModuleRegistryProxy

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__(self, services):
        common_module_manager.ModuleManager.__init__(self, services, services.type_registry_registry, services.types.packet)
        self._id2module = {}
        self._objimpl_registry = services.objimpl_registry
        self._view_registry = services.view_registry
        self._param_editor_registry = services.param_editor_registry

    def add_code_modules(self, modules):
        for module in modules:
            self.add_code_module(module)

    def add_code_module(self, module):
        log.info('-- loading module %r package=%r fpath=%r', module.id, module.package, module.fpath)
        self._id2module[module.id] = module
        self.load_code_module(module)

    def resolve_ids(self, module_ids):
        modules = []
        for id in module_ids:
            if self._type_registry_registry.has_type_registry(id): continue  # do not return type modules
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
