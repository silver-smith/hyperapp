from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry = {}  # resource name -> factory.
        services.python_object_creg = CodeRegistry('python_object', services.web, services.types)
