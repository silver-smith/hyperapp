from .code_registry import CodeRegistry
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.object_registry = CodeRegistry('object', services.async_web, services.types)
