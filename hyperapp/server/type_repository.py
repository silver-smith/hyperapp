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

        def __init__( self, type_module, type_registry ):
            assert isinstance(type_module, tTypeModule), repr(type_module)
            assert isinstance(type_registry, TypeRegistry), repr(type_registry)
            self.type_module = type_module
            self.type_registry = type_registry

    def __init__( self, dir ):
        self._class2rec = {}  # str -> _Rec
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
            if requirement[0] != 'class': continue
            module = self._class2rec.get(requirement[1])
            if module:
                modules.add(module)
        return list(module.type_module for module in modules)

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
        provided_classes = self._pick_provided_classes(typedefs)
        type_module = tTypeModule(name, provided_classes, typedefs)
        module_rec = self._Rec(type_module, type_registry)
        self._id2rec[name] = module_rec
        for rec in provided_classes:
            log.info('    provides class %s:%s', rec.hierarchy_id, rec.class_id)
            path = encode_path([rec.hierarchy_id, rec.class_id])
            self._class2rec[path] = module_rec

    def _pick_provided_classes( self, typedefs ):
        classes = []
        for typedef in typedefs:
            t = typedef.type
            log.info('    registered name %r', typedef.name)
            if not isinstance(t, tHierarchyClassMeta): continue
            assert isinstance(t.hierarchy, tNamed), repr(typedef.name)  # tHierarchyClassMeta.hierarchy must be tNamed
            classes.append(tProvidedClass(t.hierarchy.name, t.class_id))
        return classes
