from hyperapp.common.module import Module

from .cached_code_registry import CachedCodeRegistry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg = {}  # resource_t -> ResourceType instance
        services.python_object_creg = CachedCodeRegistry('python_object', services.web, services.types)
