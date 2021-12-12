import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class LegacyModuleResource:

    def __init__(self, module_name):
        self._module_name = module_name

    def __repr__(self):
        return f"<LegacyModule: {self._module_name}>"


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._register_modules(services.builtin_resource_by_name, services.local_modules, services.module_registry)

    def _register_modules(self, builtin_resource_by_name, local_modules, module_registry):
        for module_name, module in local_modules.by_name.items():
            name = module_name.split('.')[-1]
            resource = LegacyModuleResource(module_name)
            builtin_resource_by_name[name] = resource
            log.info("Legacy module resource %s: %s", name, resource)
