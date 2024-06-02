import logging

from .phony_ref import phony_ref
from .meta_type import builtin_mt

log = logging.getLogger(__name__)


class BuiltinTypeRegistry:

    def __init__(self):
        self._name_to_type = {}

    def register(self, pyobj_creg, t):
        self._name_to_type[t.name] = t
        piece = builtin_mt(t.name)
        pyobj_creg.add_to_cache(piece, t)
        log.debug("Registered builtin type %s: %s", t, piece)

    def resolve(self, name):
        return self._name_to_type[name]

    def keys(self):
        return self._name_to_type.keys()

    def values(self):
        return self._name_to_type.values()

    def type_from_piece(self, piece):
        return self._name_to_type[piece.name]

    def register_builtin_mt(self, mosaic, pyobj_creg):
        # Register builtin_mt with phony piece - can not be registered as usual because of dependency loop.
        self._name_to_type[builtin_mt.name] = builtin_mt
        builtin_ref = phony_ref(builtin_mt.name)
        builtin_mt_piece = builtin_mt(builtin_mt.name)
        mosaic.add_to_cache(builtin_mt_piece, builtin_ref)
        pyobj_creg.add_to_cache(builtin_mt_piece, builtin_mt)
        pyobj_creg.register_actor(builtin_mt, self.type_from_piece)
