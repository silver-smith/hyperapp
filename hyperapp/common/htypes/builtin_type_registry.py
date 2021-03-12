import logging

from .meta_type import builtin_mt

log = logging.getLogger(__name__)


class BuiltinTypeRegistry:

    def __init__(self):
        self._name_to_type = {}

    def register(self, mosaic, types, t):
        self._name_to_type[t.name] = t
        piece = builtin_mt(t.name)
        type_ref = mosaic.put(piece)
        types.add_to_cache(type_ref, t)
        log.debug("Registered builtin type %s: %s", t, type_ref)

    def resolve(self, name):
        return self._name_to_type[name]

    def items(self):
        return self._name_to_type

    def type_from_piece(self, piece, type_code_registry, name):
        return self._name_to_type[piece.name]

    def register_builtin_mt(self, type_code_registry):
        type_code_registry.register_actor(builtin_mt, self.type_from_piece)
        
