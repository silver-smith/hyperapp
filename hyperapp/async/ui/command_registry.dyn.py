from hyperapp.common.module import Module

from .code_registry import CodeRegistry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.command_registry = CodeRegistry('rpc_message', services.async_web, services.types)
