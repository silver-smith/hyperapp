from .htypes import register_builtin_meta_types, register_meta_types
from .htypes.legacy_type import legacy_type_t
from .cached_code_registry import CachedCodeRegistry


class PyObjRegistry(CachedCodeRegistry):

    def __init__(self, association_reg):
        super().__init__(None, None, association_reg, self, 'pyobj')

    def init(self, builtin_types, mosaic, web):
        self._mosaic = mosaic
        self._web = web
        builtin_types.register_builtin_mt(mosaic, self)
        register_builtin_meta_types(builtin_types, self)
        register_meta_types(self)
