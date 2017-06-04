import os
import os.path
import logging
from types import SimpleNamespace
from .util import is_list_inst, encode_path
from .htypes import (
    Interface,
    IfaceRegistry,
    tHierarchyClassMeta,
    tNamed,
    tProvidedClass,
    tTypeModule,
    tInterfaceMeta,
    TypeRegistry,
    TypeRegistryRegistry,
    TypeResolver,
    make_meta_type_registry,
    )
from .type_module import resolve_typedefs, load_types_file


log = logging.getLogger(__name__)


class TypeModuleRepository(object):

    def __init__(self, dir, request_types, iface_registry, type_registry_registry):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(type_registry_registry, TypeRegistryRegistry), repr(type_registry_registry)
        self._meta_type_registry = make_meta_type_registry()
        self._request_types = request_types
        self._iface_registry = iface_registry
        self._type_registry_registry = type_registry_registry
        self._core_types = None  # set when 'core' types module is loaded
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
        used_modules, typedefs, type_registry = load_types_file(self._meta_type_registry, self._type_registry_registry, fpath)
        provided_classes = []
        for typedef in typedefs:
            t = typedef.type
            log.info('    registered name %r: %r', typedef.name, t.type_id)
            if isinstance(t, tHierarchyClassMeta):
                assert isinstance(t.hierarchy, tNamed), repr(typedef.name)  # tHierarchyClassMeta.hierarchy must be tNamed
                pclass = tProvidedClass(t.hierarchy.name, t.class_id)
                provided_classes.append(pclass)
                log.info('    provides class %s:%s', pclass.hierarchy_id, pclass.class_id)
        module = tTypeModule(name, provided_classes, used_modules, typedefs)
        self._register_type_module(module, type_registry)
        ns = SimpleNamespace(**dict(type_registry.items()))
        if name == 'core':  # we need it
            self._core_types = ns
        return ns

    def add_all_type_modules(self, type_module_list):
        assert is_list_inst(type_module_list, tTypeModule), repr(type_module_list)
        for module in type_module_list:
            if not self.has_type_module(module.module_name):
                self.add_type_module(module)

    def add_type_module(self, module):
        log.info('  adding type module %r', module.module_name)
        assert isinstance(module, tTypeModule), repr(module)
        resolver = TypeResolver(self._type_registry_registry.get_all_type_registries())
        type_registry = resolve_typedefs(self._meta_type_registry, resolver, module.typedefs)
        self._register_type_module(module, type_registry)

    def _register_type_module(self, module, type_registry):
        provided_ifaces = []
        for typedef in module.typedefs:
            if isinstance(typedef.type, tInterfaceMeta):
                provided_ifaces.append(typedef.name)
                log.info('    provides interface %r', typedef.name)
        self._class_id2type_module.update({
            encode_path([pc.hierarchy_id, pc.class_id]): module
            for pc in module.provided_classes})
        self._iface_id2type_module.update({
            name: module for name in provided_ifaces})
        self._module_id2type_module[module.module_name] = module
        self._type_registry_registry.register(module.module_name, type_registry)
        self._register_ifaces(type_registry)

    def _get_dep_modules(self, modules):
        if not modules: return []
        dep_modules = []
        for module in modules:
            dep_modules += [self.get_type_module_by_id(module_id) for module_id in module.used_modules]
        return self._get_dep_modules(dep_modules) + dep_modules

    def _register_ifaces(self, type_registry):
        for name, t in type_registry.items():
            if not isinstance(t, Interface): continue
            assert self._core_types  # 'core' module must be loaded first
            t.register_types(self._request_types, self._core_types)
            self._iface_registry.register(t)
