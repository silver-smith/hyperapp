import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class LegacyModuleResource:

    def __init__(self, module_name, module, module_registry, module_by_requirement, services):
        self._module_name = module_name
        self._module = module  # code_module_t
        self._module_registry = module_registry
        self._module_by_requirement = module_by_requirement
        self._services = services

    def __repr__(self):
        return f"<LegacyModule: {self._module_name}>"

    def value(self):
        if not self._module_registry.module_loaded(self._module):
            self._module_registry.import_module_list(self._services, [self._module], self._module_by_requirement, config_dict={})
        return self._module_registry.get_python_module(self._module)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.legacy_module_resources = {}  # module name -> code_module_t

        self._register_modules(
            services.mosaic, services.legacy_module_resources, services.builtin_resource_by_name, services.local_modules)

    def _register_modules(self, mosaic, legacy_module_resources, builtin_resource_by_name, local_modules):
        for module_name, module in local_modules.by_name.items():
            builtin_resource_by_name[module_name] = mosaic.put(module)
            legacy_module_resources[module_name] = module
            log.info("Legacy module resource %s: %s", module_name, module)
