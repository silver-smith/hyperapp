from hyperapp.common.code_module import code_module_t
from hyperapp.common.module import Module

from .legacy_module import python_object


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_acreg.register_actor(
            code_module_t, python_object, services.module_registry, services.local_modules.by_requirement, services)
