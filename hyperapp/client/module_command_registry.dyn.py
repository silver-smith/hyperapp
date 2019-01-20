from hyperapp.common.util import flatten
from hyperapp.client.module import ClientModule


MODULE_NAME = 'module_command_registry'


class ModuleCommandRegistry:

    def __init__(self, module_registry):
        self._module_registry = module_registry

    def get_all_commands(self):
        return flatten(method() for method in
                       self._module_registry.enum_modules_method('get_command_list'))

    def get_all_object_commands(self, object):
        return [command.clone(args=(object,)) for command in
                flatten(method(object) for method in
                        self._module_registry.enum_modules_method('get_object_command_list'))]
        
class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.module_command_registry = ModuleCommandRegistry(services.module_registry)
