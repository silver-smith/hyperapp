# todo: Do we really need to construct global and builtin commands from piece, command_registry?

import inspect
import weakref

from hyperapp.common.module import Module

from . import htypes


class GlobalCommand:

    @classmethod
    def from_class_method(cls, method):
        module_ref = inspect.getmodule(method).__module_ref__
        assert method.__qualname__.startswith('ThisModule.')  # Only ThisModule name is expected for client modules.
        attr_name = method.__name__
        return cls(module_ref, attr_name)

    def __init__(self, module_ref, name):
        self._module_ref = module_ref
        self.name = name

    @property
    def piece(self):
        return htypes.command.global_command(self._module_ref, self.name)

    def __repr__(self):
        return f"Global:{self.name}@{self._module_ref}"

    async def run(self):
        module = this_module.module_ref_to_module[self._module_ref]
        method = getattr(module.this_module, self.name)
        return await method()


class ClientModule(Module):

    def __init__(self, name, services, config):
        super().__init__(name, services, config)
        self._init_commands()

    def _init_commands(self):
        cls = type(self)
        for name in dir(cls):
            if name.startswith('__'):
                continue
            attr = getattr(cls, name)
            if type(attr) is property:
                continue  # Avoid to call properties as we are not yet fully constructed.
            if getattr(attr, '__is_command__', False):
                this_module.global_command_list.append(
                    GlobalCommand.from_class_method(attr))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self.module_ref_to_module = services.code_module_importer.registry
        self.global_command_list = []
        services.global_command_list = self.global_command_list
