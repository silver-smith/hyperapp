import os.path
import sys
import importlib
from hyperapp.common.htypes import (
    IfaceRegistry,
    TypeRegistryRegistry,
    builtin_type_registry,
    make_request_types,
    )
from hyperapp.common.type_repository import TypeRepository


TYPE_MODULE_EXT = '.types'


class ServicesBase(object):

    def init_services( self ):
        self.request_types = make_request_types()
        self.iface_registry = IfaceRegistry()
        self.type_registry_registry = TypeRegistryRegistry(dict(builtins=builtin_type_registry()))
        self.type_repository = TypeRepository(self.interface_dir, self.request_types, self.iface_registry, self.type_registry_registry)

    def _load_core_type_module( self ):
        self._load_type_module('core')
        core_types = sys.modules.get('hyperapp.common.interface.core')
        if core_types:
            self.core_types = importlib.reload(core_types)
        else:
            self.core_types = importlib.import_module('hyperapp.common.interface.core')
        # fails if previous ModuleManager import hook was not unregistered
        assert self.core_types.object is self.type_registry_registry.resolve_type_registry('core').resolve('object')

    def _load_type_module( self, module_name ):
        fpath = os.path.join(self.interface_dir, module_name + TYPE_MODULE_EXT)
        self.type_repository.load_module(module_name, fpath)
        
    def _load_type_modules( self, module_name_list ):
        for module_name in module_name_list:
            self._load_type_module(module_name)
