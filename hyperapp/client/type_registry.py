from ..common.htypes import tTypeModule


class TypeRegistry(object):

    def __init__( self ):
        self._registry = {}  # module name -> tTypeModule

    def register( self, type_module ):
        assert isinstance(type_module, tTypeModule), repr(type_module)
        self._registry[type_module.module_name] = type_module

    def has_module( self, module_name ):
        return module_name in self._registry

    def resolve( self, module_name ):
        return self._registry[module_name]
