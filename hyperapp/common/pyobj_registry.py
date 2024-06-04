from .htypes import register_builtin_meta_types, register_meta_types
from .cached_code_registry import CachedCodeRegistry


class PyObjRegistry(CachedCodeRegistry):

    def __init__(self, association_reg, reconstructors):
        super().__init__(None, None, association_reg, self, 'pyobj')
        self._reconstructors = reconstructors

    def init(self, builtin_types, mosaic, web):
        self._mosaic = mosaic
        self._web = web
        builtin_types.register_builtin_mt(mosaic, self)
        register_builtin_meta_types(builtin_types, self)
        register_meta_types(self)

    def actor_to_piece(self, actor):
        try:
            return super().actor_to_piece(actor)
        except KeyError:
            for rctr in self._reconstructors:
                piece = rctr(actor)
                if piece is not None:
                    self.add_to_cache(piece, actor)
                    return piece
            raise
