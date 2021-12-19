import logging

from hyperapp.common.code_module import code_module_t
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


def python_object(piece, module_registry, module_by_requirement, services):
    if not module_registry.module_loaded(piece):
        module_registry.import_module_list(services, [piece], module_by_requirement, config_dict={})
    return module_registry.get_python_module(piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._register_modules(
            services.mosaic, services.builtin_resource_by_name, services.local_modules)
        services.python_object_creg.register_actor(
            code_module_t, python_object, services.module_registry, services.local_modules.by_requirement, services)

    def _register_modules(self, mosaic, builtin_resource_by_name, local_modules):
        for module_name, module in local_modules.by_name.items():
            builtin_resource_by_name[module_name] = mosaic.put(module)
            log.info("Legacy module resource %s: %s", module_name, module)
