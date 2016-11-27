import os
import os.path
import logging
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    Interface,
    IfaceRegistry,
    tHierarchyMeta,
    tHierarchyClassMeta,
    tNamed,
    tProvidedClass,
    tTypeModule,
    tInterfaceMeta,
    TypeRegistry,
    TypeRegistryRegistry,
    make_meta_type_registry,
    builtin_type_registry,
    )
from ..common.type_module import load_types_file
from ..common import module_manager as common_module_manager


log = logging.getLogger(__name__)


class TypeRepository(object):

    def __init__( self, dir, iface_registry, type_registry_registry ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(type_registry_registry, TypeRegistryRegistry), repr(type_registry_registry)
        self._iface_registry = iface_registry
        self._type_registry_registry = type_registry_registry
        self._class2type_module = {}  # str -> tTypeModule
        self._iface2type_module = {}  # str -> tTypeModule
        self._id2type_module = {}  # str -> tTypeModule

    def has_module_id( self, module_id ):
        return module_id in self._id2type_module

    def get_module_by_id( self, module_id ):
        return self._id2type_module[module_id]

    def get_modules_by_requirements( self, requirements ):
        class_paths = set(requirement[1] for requirement in requirements)
        modules = set()
        for requirement in requirements:
            if requirement[0] == 'class':
                module = self.get_class_module_by_requirement(requirement[1])
            elif requirement[0] == 'interface':
                module = self.get_type_module_by_requirement(requirement[1])
            else:
                continue
            if module:
                modules.add(module)
        return list(modules)

    def get_class_module_by_requirement( self, key ):
        return self._class2type_module.get(key)

    def get_type_module_by_requirement( self, key ):
        return self._iface2type_module.get(key)
    
    def has_module( self, module_name ):
        return self.has_module_id(module_name)

    def load_module( self, name, fpath ):
        log.info('loading type module %r from %r', name, fpath)
        used_modules, typedefs, type_registry = load_types_file(make_meta_type_registry(), self._type_registry_registry, fpath)
        provided_classes = []
        provided_ifaces = []
        for typedef in typedefs:
            t = typedef.type
            log.info('    registered name %r: %r', typedef.name, t.type_id)
            if isinstance(t, tHierarchyClassMeta):
                assert isinstance(t.hierarchy, tNamed), repr(typedef.name)  # tHierarchyClassMeta.hierarchy must be tNamed
                pclass = tProvidedClass(t.hierarchy.name, t.class_id)
                provided_classes.append(pclass)
                log.info('    provides class %s:%s', pclass.hierarchy_id, pclass.class_id)
            if isinstance(t, tInterfaceMeta):
                provided_ifaces.append(typedef.name)
                log.info('    provides interface %r', typedef.name)
        type_module = tTypeModule(name, provided_classes, used_modules, typedefs)
        self._class2type_module.update({
            encode_path([pc.hierarchy_id, pc.class_id]): type_module
            for pc in provided_classes})
        self._iface2type_module.update({
            name: type_module for name in provided_ifaces})
        self._type_registry_registry.register(name, type_registry)
        self._register_ifaces(type_registry)

    def _register_ifaces( self, type_registry ):
        for name, t in type_registry.items():
            if not isinstance(t, Interface): continue
            self._iface_registry.register(t)
