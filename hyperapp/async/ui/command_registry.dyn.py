from hyperapp.common.module import Module

from .code_registry import CodeRegistry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.command_registry = CodeRegistry('command', services.async_web, services.types)
