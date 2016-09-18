import os
import os.path
import logging
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    tHierarchyMeta,
    tHierarchyClassMeta,
    tNamed,
    tProvidedClass,
    tTypeModule,
    tInterfaceMeta,
    TypeRegistry,
    make_meta_type_registry,
    builtin_type_registry,
    )
from ..common.type_module import load_types_file
from ..common import module_manager as common_module_manager


log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'


class TypeRepository(common_module_manager.TypeModuleRegistry):

    class _Rec(object):

        def __init__( self, type_registry ):
            assert isinstance(type_registry, TypeRegistry), repr(type_registry)
            self.type_registry = type_registry

        def set_type_module( self, type_module ):
            assert isinstance(type_module, tTypeModule), repr(type_module)
            self.type_module = type_module

    def __init__( self, dir ):
        self._class2rec = {}  # str -> _Rec
        self._iface2rec = {}  # str -> _Rec
        self._id2rec = {}  # str -> _Rec
        self._load_modules(dir)

    def has_module_id( self, module_id ):
        return module_id in self._id2rec

    def get_module_by_id( self, module_id ):
        return self._id2rec[module_id].type_module

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
        if key in self._class2rec:
            return self._class2rec[key].type_module
        else:
            return None

    def get_type_module_by_requirement( self, key ):
        if key in self._iface2rec:
            return self._iface2rec[key].type_module
        else:
            return None
    
    def has_module( self, module_name ):
        return self.has_module_id(module_name)

    def resolve_type_registry( self, name ):
        return self._id2rec[name].type_registry

    def _load_modules( self, dir ):
        for fname in os.listdir(dir):
            if fname.endswith(TYPE_MODULE_EXT):
                name = fname.split('.')[0]
                self._load_module(name, os.path.join(dir, fname))

    def _load_module( self, name, fpath ):
        log.info('loading type module %r from %r', name, fpath)
        typedefs, type_registry = load_types_file(make_meta_type_registry(), builtin_type_registry(), fpath)
        module_rec = self._Rec(type_registry)
        provided_classes = []
        for typedef in typedefs:
            t = typedef.type
            log.info('    registered name %r: %r', typedef.name, t.type_id)
            if isinstance(t, tHierarchyClassMeta):
                assert isinstance(t.hierarchy, tNamed), repr(typedef.name)  # tHierarchyClassMeta.hierarchy must be tNamed
                pclass = tProvidedClass(t.hierarchy.name, t.class_id)
                provided_classes.append(pclass)
                path = encode_path([pclass.hierarchy_id, pclass.class_id])
                self._class2rec[path] = module_rec
                log.info('    provides class %s:%s', pclass.hierarchy_id, pclass.class_id)
            if isinstance(t, tInterfaceMeta):
                self._iface2rec[typedef.name] = module_rec
                log.info('    provides interface %r', typedef.name)
        module_rec.set_type_module(tTypeModule(name, provided_classes, typedefs))
        self._id2rec[name] = module_rec
