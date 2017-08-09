import os.path
import sys
from types import SimpleNamespace
from hyperapp.common.htypes import (
    IfaceRegistry,
    builtin_type_registry_registry,
    )
from hyperapp.common.type_module_repository import TypeModuleRepository


TYPE_MODULE_EXT = '.types'


class ServicesBase(object):

    def init_services(self):
        self.types = SimpleNamespace()
        self.iface_registry = IfaceRegistry()
        self.type_registry_registry = builtin_type_registry_registry()
        self.type_module_repository = TypeModuleRepository(self.iface_registry, self.type_registry_registry)

    def _load_type_module(self, module_name):
        fpath = os.path.join(self.interface_dir, module_name + TYPE_MODULE_EXT)
        ns = self.type_module_repository.load_type_module(module_name, fpath)
        setattr(self.types, module_name, ns)
        
    def _load_type_modules(self, module_name_list):
        for module_name in module_name_list:
            self._load_type_module(module_name)
