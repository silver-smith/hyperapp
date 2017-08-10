from .command_class import Commander


class Module(Commander):

    def __init__(self, services):
        Commander.__init__(self, commands_kind='global')

    def get_object_commands(self, object):
        return []


class ModuleRegistry(object):

    def __init__(self):
        self._modules = []

    def register(self, module):
        assert isinstance(module, Module), repr(module)
        self._modules.append(module)

    def get_all_commands(self):
        commands = []
        for module in self._modules:
            commands += module.get_commands()
        return commands

    def get_all_object_commands(self, object):
        commands = []
        for module in self._modules:
            commands += module.get_object_commands(object)
        return [cmd.clone(args=(object,)) for cmd in commands]
