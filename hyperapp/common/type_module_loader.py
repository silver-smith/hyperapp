import uuid
from .htypes import (
    ref_t,
    tNamed,
    t_ref,
    builtin_ref_t,
    meta_ref_t,
    )
from .type_module_parser import load_type_module
from .local_type_module import LocalTypeModule
from .mapper import Mapper


class _TypeModuleToRefsMapper(Mapper):

    def __init__(self, type_resolver, ref_registry, local_name_dict):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._local_name_dict = local_name_dict

    def map_hierarchy_obj(self, tclass, value):
        if tclass is tNamed:
            return self._map_named_t(value)
        return value

    def _map_named_t(self, rec):
        ref = self._local_name_dict.get(rec.name)
        if ref:
            return t_ref(ref)
        t = self._type_resolver.builtin_type_by_name[rec.name]
        return t_ref(self._make_builtin_type_ref(t))

    def _make_builtin_type_ref(self, t):
        rec = builtin_ref_t(t.name)
        return self._ref_registry.register_object(rec)  # expected fail for duplicates; todo: move ref to Type


class TypeModuleLoader(object):

    def __init__(self, type_resolver, ref_registry, local_type_module_registry):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._local_type_module_registry = local_type_module_registry

    def load_type_module(self, name, path):
        source_module = load_type_module(name, path)
        local_type_module = self._map_type_module_to_refs(source_module)
        self._local_type_module_registry.register(name, local_type_module)

    def _map_type_module_to_refs(self, module):
        local_name_dict = {}  # name -> ref
        for import_ in module.import_list:
            imported_module = self._local_type_module_registry[import_.module_name]
            local_name_dict[import_.name] = imported_module[import_.name]
        local_type_module = LocalTypeModule()
        mapper = _TypeModuleToRefsMapper(self._type_resolver, self._ref_registry, local_name_dict)
        for typedef in module.typedefs:
            t = mapper.map(typedef.type)
            rec = meta_ref_t(
                name=typedef.name,
                random_salt=uuid.uuid4().bytes,
                type=t,
                )
            ref = self._ref_registry.register_object(rec)
            local_type_module.register(typedef.name, ref)
            local_name_dict[typedef.name] = ref
        return local_type_module

