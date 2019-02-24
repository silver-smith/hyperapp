import logging

from .htypes import (
    ref_t,
    tNamed,
    t_ref,
    builtin_ref_t,
    meta_ref_t,
    )
from .ref import ref_repr
from .visual_rep import pprint
from .type_module_parser import load_type_module_source
from .local_type_module import LocalTypeModule
from .mapper import Mapper

log = logging.getLogger(__name__)


class _NameToRefMapper(Mapper):

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

    def load_type_module(self, path, name=None):
        name = name or path.stem
        source = load_type_module_source(path, name)
        local_type_module = self._map_names_to_refs(name, source)
        self._local_type_module_registry.register(name, local_type_module)

    def _map_names_to_refs(self, module_name, module_source):
        local_name_dict = {}  # name -> ref
        for import_ in module_source.import_list:
            imported_module = self._local_type_module_registry[import_.module_name]
            try:
                local_name_dict[import_.name] = imported_module[import_.name]
            except KeyError:
                raise RuntimeError('Module {0!r} wants name {1!r} from module {2!r}, but module {2!r} does not have it'.format(
                    module_name, import_.module_name, import_.name))
        local_type_module = LocalTypeModule()
        mapper = _NameToRefMapper(self._type_resolver, self._ref_registry, local_name_dict)
        for typedef in module_source.typedefs:
            t = mapper.map(typedef.type)
            rec = meta_ref_t(
                name=typedef.name,
                type=t,
                )
            ref = self._ref_registry.register_object(rec)
            local_type_module.register(typedef.name, ref)
            local_name_dict[typedef.name] = ref
            log.debug('Type module loader: %r is mapped to %s:', typedef.name, ref_repr(ref))
            pprint(rec)
        return local_type_module

