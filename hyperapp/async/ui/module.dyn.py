# todo: Do we really need to construct global and builtin commands from piece, command_registry?

import inspect
import weakref

from hyperapp.common.module import Module

from . import htypes


class GlobalCommand:

    @classmethod
    def from_instance_method(cls, module_name, method):
        assert method.__qualname__.startswith('ThisModule.')  # Only ThisModule name is expected for client modules.
        attr_name = method.__name__
        return cls(module_name, attr_name, method)

    def __init__(self, module_name, name, method):
        self._module_name = module_name
        self.name = name
        self._method = method

    @property
    def dir(self):
        return [htypes.command.module_d(self._module_name), htypes.command.global_command_d(self.name)]

    def __repr__(self):
        return f"Global:{self.name}@{self._module_name}"

    async def run(self):
        return await self._method()


class ClientModule(Module):

    def __init__(self, name, services, config):
        super().__init__(name, services, config)
        self._init_commands()

    def _init_commands(self):
        cls = type(self)
        for name in dir(self):
            if name.startswith('__'):
                continue
            if hasattr(cls, name) and type(getattr(cls, name)) is property:
                continue  # Avoid to call properties as we are not yet fully constructed.
            attr = getattr(self, name)
            if getattr(attr, '__is_command__', False):
                this_module.global_command_list.append(
                    GlobalCommand.from_instance_method(self.name, attr))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self.global_command_list = []
        services.global_command_list = self.global_command_list
