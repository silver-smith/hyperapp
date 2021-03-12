import logging

from .htypes import (
    ref_t,
    name_mt,
    name_wrapped_mt,
    )
from .ref import ref_repr
from .visual_rep import pprint
from .type_module_parser import load_type_module_source
from .local_type_module import LocalTypeModule
from .mapper import Mapper

log = logging.getLogger(__name__)


class _NameToRefMapper(Mapper):

    def __init__(self, types, mosaic, local_name_dict):
        self._types = types
        self._mosaic = mosaic
        self._local_name_dict = local_name_dict

    def map_record(self, t, value):
        if t is name_mt:
            return self._resolve_name(value)
        if t is ref_t:
            return self._map_ref(value)
        return value

    def _resolve_name(self, rec):
        ref = self._local_name_dict.get(rec.name)
        if not ref:
            ref = self._types.get_builtin_type_ref(rec.name)
        piece = self._mosaic.resolve_ref(ref).value
        log.debug("Name %r is resolved to %s %r", rec.name, ref, piece)
        return piece

    def _map_ref(self, ref):
        piece = self._mosaic.resolve_ref(ref).value
        log.debug("Ref %s is resolved to %r", ref, piece)
        mapped_piece = self.map(piece)
        log.debug("Ref %s %s is mapped to %r", ref, piece, mapped_piece)
        return self._mosaic.put(mapped_piece)


class TypeModuleLoader(object):

    def __init__(self, types, mosaic, local_type_module_registry):
        self._types = types
        self._mosaic = mosaic
        self._local_type_module_registry = local_type_module_registry

    def load_type_module(self, path, name=None):
        log.info("Load type module %r: %s", name, path)
        name = name or path.stem
        source = load_type_module_source(self._mosaic, path, name)
        local_type_module = self._map_names_to_refs(name, source)
        self._local_type_module_registry.register(name, local_type_module)

    def _map_names_to_refs(self, module_name, module_source):
        local_name_dict = {}  # name -> ref
        for import_ in module_source.import_list:
            try:
                imported_module = self._local_type_module_registry[import_.module_name]
            except KeyError:
                raise RuntimeError(
                    f"Type module {module_name!r} wants name {import_.name!r} from module {import_.module_name!r},"
                    f" but module {import_.module_name!r} does not exist")
            try:
                local_name_dict[import_.name] = imported_module[import_.name]
            except KeyError:
                raise RuntimeError(
                    f"Type module {module_name!r} wants name {import_.name!r} from module {import_.module_name!r},"
                    f" but module {import_.module_name!r} does not have it")
        local_type_module = LocalTypeModule()
        mapper = _NameToRefMapper(self._types, self._mosaic, local_name_dict)
        for typedef in module_source.typedefs:
            log.debug('Type module loader %r: mapping %r %s:', module_name, typedef.name, typedef.type)
            type_ref = mapper.map(typedef.type)
            named = name_wrapped_mt(typedef.name, type_ref)
            ref = self._mosaic.put(named)
            local_type_module.register(typedef.name, ref)
            local_name_dict[typedef.name] = ref
            log.debug('Type module loader %r: %r is mapped to %s', module_name, typedef.name, ref)
        return local_type_module
