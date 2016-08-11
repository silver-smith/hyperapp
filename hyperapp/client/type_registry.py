from ..common.util import encode_path
from ..common.htypes import tTypeModule


class TypeRegistry(object):

    def __init__( self ):
        self._name2module = {}  # module name -> tTypeModule
        self._class2module = {}  # encoded hierarchy_id|class_id -> tTypeModule

    def register( self, type_module ):
        assert isinstance(type_module, tTypeModule), repr(type_module)
        self._name2module[type_module.module_name] = type_module
        for rec in type_module.provided_classes:
            self._class2module[encode_path([rec.hierarchy_id, rec.class_id])] = type_module

    def get_dynamic_module_id( self, id ):
        type_module = self._class2module.get(id)
        if not type_module:
            return None
        return type_module.module_name

    def has_module( self, module_name ):
        return module_name in self._name2module

    def resolve( self, module_name ):
        return self._name2module[module_name]
