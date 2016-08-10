import os
import os.path
import logging
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    tHierarchyMeta,
    tHierarchyClassMeta,
    tNamed,
    )
from ..common.type_module import tTypeDef, load_types_from_yaml_file

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types.yaml'


class TypeRepository(object):

    class _Rec(object):

        def __init__( self, typedefs ):
            assert is_list_inst(typedefs, tTypeDef), repr(typedefs)
            self.typedefs = typedefs

    def __init__( self, dir ):
        self._requirement2module = {}  # str -> _Rec
        self._load_modules(dir)

    def _load_modules( self, dir ):
        for fname in os.listdir(dir):
            if fname.endswith(TYPE_MODULE_EXT):
                log.info('loading type module: %r', fname)
                self._load_module(os.path.join(dir, fname))

    def _load_module( self, fpath ):
        typedefs = load_types_from_yaml_file(fpath)
        for requirement in self._pick_provided_requirements(typedefs):
            log.info('    provides class %r', requirement)
            self._requirement2module[requirement] = self._Rec(typedefs)

    def _pick_provided_requirements( self, typedefs ):
        requirements = []
        for typedef in typedefs:
            t = typedef.type
            if not isinstance(t, tHierarchyClassMeta): continue
            assert isinstance(t.hierarchy, tNamed), repr(name)  # tHierarchyClassMeta.hierarchy must be tNamed
            requirements.append(encode_path([t.hierarchy.name, t.class_id]))
        return requirements
