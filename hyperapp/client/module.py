from ..common.module_registry import ModuleRegistry
from ..common.module import Module
from .command_class import Commander


class ClientModule(Module, Commander):

    def __init__(self, name, services):
        Module.__init__(self, name)
        Commander.__init__(self, commands_kind='global')

    async def async_init(self, services):
        pass

    def get_object_command_list(self, object, kinds=None):
        return []


class ClientModuleRegistry(ModuleRegistry):

    def __init__(self):
        self._modules = []

    def register(self, module):
        assert isinstance(module, Module), repr(module)
        self._modules.append(module)

    def _enum_client_modules(self):
        for module in self._modules:
            if isinstance(module, ClientModule):
                yield module

    async def async_init(self, services):
        for module in self._enum_client_modules():
            await module.async_init(services)

    def get_all_commands(self):
        commands = []
        for module in self._enum_client_modules():
            commands += module.get_command_list()
        return commands

    def get_all_object_commands(self, object):
        commands = []
        for module in self._enum_client_modules():
            commands += module.get_object_command_list(object)
        return [cmd.clone(args=(object,)) for cmd in commands]
