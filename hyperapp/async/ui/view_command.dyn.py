import inspect

from . import htypes


class ViewCommand:

    kind = 'view'

    @classmethod
    def from_bound_method(cls, method):
        module_ref = inspect.getmodule(method).__module_ref__
        qual_name = method.__qualname__
        attr_name = method.__name__
        return cls(module_ref, qual_name, attr_name, method)

    def __init__(self, module_ref, qual_name, name, method):
        self._module_ref = module_ref
        self._qual_name = qual_name
        self.name = name
        self._method = method

    def __repr__(self):
        return f"ViewCommand({self._module_ref}/{self._qual_name})"

    @property
    def piece(self):
        return htypes.command.view_command(
            self._module_ref, self._qual_name)

    async def run(self):
        await self._method()


class ViewCommander:

    def __init__(self):
        self._command_list = []
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
                self._command_list.append(ViewCommand.from_bound_method(attr))

    def get_command_list(self):
        return self._command_list

    def get_all_command_list(self):
        return self._command_list
