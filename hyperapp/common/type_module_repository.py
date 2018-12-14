import os
import os.path
import logging
import sys
import importlib

from .util import is_list_inst, encode_path
from .htypes import (
    Interface,
    tHierarchyClassMeta,
    tNamed,
    tProvidedClass,
    tTypeModule,
    tInterfaceMeta,
    TypeNamespace,
    )
from .type_module_parser import load_type_module
from .local_type_module import resolve_type_module

log = logging.getLogger(__name__)


TYPE_MODULES_PACKAGE = 'hyperapp.common.interface'


class TypeModuleRepository(object):

    def __init__(self, types):
        assert isinstance(types, TypeNamespace), repr(types)
        self._types = types
        self._class_id2type_module = {}  # str -> tTypeModule
        self._iface_id2type_module = {}  # str -> tTypeModule
        self._module_id2type_module = {}  # str -> tTypeModule

    def has_type_module(self, module_id):
        return module_id in self._module_id2type_module

    def get_type_module_by_id(self, module_id):
        assert self.has_type_module(module_id), 'Unknown module id: %r; known are: %r' % (module_id, list(self._module_id2type_module.keys()))
        return self._module_id2type_module[module_id]

    def get_type_module_by_id_with_deps(self, module_id):
        module = self.get_type_module_by_id(module_id)
        return self._get_dep_modules([module]) + [module]
    
    def get_type_modules_by_requirements(self, requirements):
        class_paths = set(requirement[1] for requirement in requirements)
        modules = set()
        for requirement in requirements:
            if requirement[0] == 'class':
                module = self._get_type_module_by_class_id(requirement[1])
            elif requirement[0] == 'interface':
                module = self.get_type_module_by_interface_id(requirement[1])
            else:
                continue
            if module:
                modules.add(module)
        return self._get_dep_modules(modules) + list(modules)

    def _get_type_module_by_class_id(self, key):
        return self._class_id2type_module.get(key)

    def get_type_module_by_interface_id(self, key):
        return self._iface_id2type_module.get(key)

    def get_type_module_id_by_class_id(self, key):
        module = self._get_type_module_by_class_id(key)
        return module.module_name if module else None

    def get_type_module_id_by_interface_id(self, key):
        module = self.get_type_module_by_interface_id(key)
        return module.module_name if module else None
    
    def load_type_module(self, name, fpath):
        log.info('loading type module %r from %r', name, fpath)
        module = load_type_module(self._types.builtins, name, fpath)
        return self._register_type_module(module)

    def add_all_type_modules(self, type_module_list):
        assert is_list_inst(type_module_list, tTypeModule), repr(type_module_list)
        for module in type_module_list:
            if not self.has_type_module(module.module_name):
                self.add_type_module(module)

    def add_type_module(self, module):
        log.info('  adding type module %r', module.module_name)
        assert isinstance(module, tTypeModule), repr(module)
        return self._register_type_module(module)

    def _register_type_module(self, module):
        provided_ifaces = []
        for typedef in module.typedefs:
            if isinstance(typedef.type, tInterfaceMeta):
                provided_ifaces.append(typedef.name)
                log.debug('    provides interface %r', typedef.name)
        self._class_id2type_module.update({
            encode_path([pc.hierarchy_id, pc.class_id]): module
            for pc in module.provided_classes})
        self._iface_id2type_module.update({
            name: module for name in provided_ifaces})
        self._module_id2type_module[module.module_name] = module
        ns = resolve_type_module(self._types, module)
        self._types[module.module_name] = ns
        fullname = TYPE_MODULES_PACKAGE + '.' + module.module_name
        if fullname in sys.modules:  # already loaded - must reload, or old one will be used by reloaded code modules
            log.debug('  reloading module %r', fullname)
            importlib.reload(sys.modules[fullname])
        return ns

    def _get_dep_modules(self, modules):
        if not modules: return []
        dep_modules = []
        for module in modules:
            dep_modules += [self.get_type_module_by_id(module_id) for module_id in module.used_modules
                            if not self._type_registry_registry.is_builtin_module(module_id)]
        return self._get_dep_modules(dep_modules) + dep_modules
