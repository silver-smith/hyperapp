from .htypes.legacy_type import legacy_type_t
from .cached_code_registry import CachedCodeRegistry


class PyObjRegistry(CachedCodeRegistry):

    def __init__(self, mosaic, web, types, association_reg):
        super().__init__(mosaic, web, types, association_reg, self, 'pyobj')

    def reverse_resolve(self, actor):
        try:
            return super().reverse_resolve(actor)
        except KeyError:
            pass
        try:
            type_ref = self._types.reverse_resolve(actor)
        except KeyError:
            raise  # Not a known type.
        type_piece = legacy_type_t(type_ref)
        self.add_to_cache(type_piece, actor)
        return type_piece
