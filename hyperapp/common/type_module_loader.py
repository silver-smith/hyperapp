import logging

from .htypes import (
    ref_t,
    name_mt,
    name_wrapped_mt,
    )
from .ref import ref_repr
from .visual_rep import pprint
from .type_module_parser import RecordMtGenerator, load_type_module_source
from .mapper import Mapper

log = logging.getLogger(__name__)


class CircularDepError(RuntimeError):
    pass


class _NameToRefMapper(Mapper):

    def __init__(self, builtin_types, mosaic, pyobj_creg, local_name_dict):
        self._builtin_types = builtin_types
        self._mosaic = mosaic
        self._pyobj_creg = pyobj_creg
        self._local_name_dict = local_name_dict

    def map_record(self, t, value, context):
        if t is name_mt:
            return self._resolve_name(value)
        if t is ref_t:
            return self._map_ref(value)
        return value

    def _resolve_name(self, rec):
        piece = self._local_name_dict.get(rec.name)
        if not piece:
            t = self._builtin_types.resolve(rec.name)
            piece = self._pyobj_creg.reverse_resolve(t)
        log.debug("Name %r is resolved to %r", rec.name, piece)
        return piece

    def _map_ref(self, ref):
        piece = self._mosaic.resolve_ref(ref).value
        log.debug("Ref %s is resolved to %r", ref, piece)
        mapped_piece = self.map(piece)
        log.debug("Ref %s %s is mapped to %r", ref, piece, mapped_piece)
        return self._mosaic.put(mapped_piece)


class TypeModuleLoader(object):

    def __init__(self, builtin_types, mosaic, pyobj_creg):
        self._builtin_types = builtin_types
        self._mosaic = mosaic
        self._pyobj_creg = pyobj_creg

    # registry: module name -> name -> name_wrapped_mt ref
    def load_type_modules(self, dir_list, registry):
        log.info("Load type modules from: %s", dir_list)
        name_to_source = self._load_sources(dir_list)  # name -> type_module_t.
        for name, source in sorted(name_to_source.items()):
            module = self._resolve_module(name_to_source, registry, name, [])
            registry[name] = module

    def _load_sources(self, dir_list):
        name_to_source = {}
        for root_dir in dir_list:
            for path in root_dir.rglob('*.types'):
                if 'test' in path.relative_to(root_dir).parts:
                    continue  # Skip test subdirectories.
                name = path.stem  # module name
                source = load_type_module_source(self._builtin_types, self._mosaic, path, name)
                name_to_source[name] = source
        return name_to_source

    def _resolve_module(self, name_to_source, name_to_module, name, dep_stack):
        if name in dep_stack:
            raise CircularDepError("Circular type module dependency: {}".format('->'.join([*dep_stack, name])))
        try:
            return name_to_module[name]  # Already mapped?
        except KeyError:
            pass
        log.debug("Resolve type module: %s", name)
        try:
            source = name_to_source[name]
        except KeyError:
            raise RuntimeError(f"Attempt to import unknown type module: {name}")
        try:
            local_name_dict = self._resolve_module_imports(name_to_source, name_to_module, source, [*dep_stack, name])
        except CircularDepError:
            raise
        except Exception as x:
            raise RuntimeError(f"Error resolving type module {name}: {x}")
        local_type_module = self._map_module_names(name, source, local_name_dict)
        return local_type_module

    def _resolve_module_imports(self, name_to_source, name_to_module, source, dep_stack):
        local_name_dict = {}  # name -> ref
        for import_def in source.import_list:
            imported_module = self._resolve_module(
                name_to_source, name_to_module, import_def.module_name, dep_stack)
            local_name_dict[import_def.target_name] = imported_module[import_def.source_name]
        return local_name_dict

    def _map_module_names(self, name, source, local_name_dict):
        local_type_module = {}
        mapper = _NameToRefMapper(self._builtin_types, self._mosaic, self._pyobj_creg, local_name_dict)
        for typedef in source.typedefs:
            log.debug('Type module loader %r: mapping %r %s:', name, typedef.name, typedef.type)
            mt = typedef.type
            if isinstance(mt, RecordMtGenerator):
                mt = mt.generate(name, typedef.name)
            piece = mapper.map(mt)
            local_type_module[typedef.name] = piece
            local_name_dict[typedef.name] = piece
            log.debug('Type module loader %r: %r is mapped to %r', name, typedef.name, piece)
        return local_type_module
