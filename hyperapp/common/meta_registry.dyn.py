from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.meta_registry = CodeRegistry('meta', services.web, services.types)
