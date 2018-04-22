import logging
from ..common import module_registry as common_module_registry
from ..common.module import Module
from .util import Path

log = logging.getLogger(__name__)


class ModuleCommand(object):

    def __init__(self, id, text, desc, shortcut, module_name):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.module_name = module_name


# base class for modules
class ServerModule(Module):

    def init_phase2(self):
        pass

    def init_phase3(self):
        pass

    def resolve(self, iface, path):
        path.raise_not_found()

    def get_commands(self):
        return []

    def run_command(self, request, command_id):
        raise RuntimeError('Unknown command: %r' % command_iid)
    
    def make_path(self, *args):
        return [self.name] + list(args)


class ModuleRegistry(common_module_registry.ModuleRegistry):

    def __init__(self):
        self._module_list = []
        self._name2module = {}

    def register(self, module):
        assert isinstance(module, Module), repr(module)
        self._module_list.append(module)  # preserves import order
        self._name2module[module.name] = module

    def init_phases(self):
        for module in self._module_list:
            if isinstance(module, ServerModule):
                module.init_phase2()
        for module in self._module_list:
            if isinstance(module, ServerModule):
                module.init_phase3()

    def get_module_by_name(self, name):
        return self._name2module[name]

    def run_resolver(self, iface, path):
        path = Path(path)
        module = path.pop_str()
        return self._name2module[module].resolve(iface, path)

    def get_all_modules_commands(self):
        commands = []
        for module in self._module_list:
            commands += module.get_commands()
        return commands
