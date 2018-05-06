# registry for transient references

import logging

from .interface import hyper_ref as href_types
from .ref import ref_repr, make_piece, make_ref
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):

    def __init__(self):
        self._registry = {}  # ref -> piece

    def register(self, piece):
        assert isinstance(piece, href_types.piece), repr(piece)
        ref = make_ref(piece)
        existing_piece = self._registry.get(ref)
        if existing_piece:
            assert piece == existing_piece, repr((existing_piece, piece))  # new piece does not match existing one
        self._registry[ref] = piece
        return ref

    def register_object(self, t, object):
        piece = make_piece(t, object)
        return self.register(piece)
        log.debug('Registered ref for %s: %s', '.'.join(t.full_name), ref_repr(ref))
        return ref

    def register_piece_list(self, piece_list):
        for piece in piece_list:
            self.register(piece)

    def register_bundle(self, bundle):
        self.register_piece_list(bundle.piece_list)

    def resolve_ref(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = ref_registry = RefRegistry()
        services.ref_resolver.add_source(ref_registry)
