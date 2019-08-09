from hyperapp.common.util import flatten
from hyperapp.client.module import ClientModule


class ModuleCommandRegistry:

    def __init__(self, module_registry):
        self._module_registry = module_registry

    def get_all_commands(self):
        return flatten(method() for method in
                       self._module_registry.enum_modules_method('get_command_list'))

    def get_all_object_commands(self, object):
        # todo: command.clone is gone, use special wrapper command class or think about another way
        return [command.clone(args=(object,)) for command in
                flatten(method(object) for method in
                        self._module_registry.enum_modules_method('get_object_command_list'))]
        
class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.module_command_registry = ModuleCommandRegistry(services.module_registry)
