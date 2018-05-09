import logging

from ..common.interface import hyper_ref as href_types
from ..common.htypes import Type
from ..common.packet_coders import packet_coders

log = logging.getLogger(__name__)


class Registry(object):

    class _Rec(object):

        def __init__(self, factory, args, kw):
            self.factory = factory  # factory functon
            self.args = args
            self.kw = kw

    def __init__(self):
        self._registry = {}  # id -> _Rec

    def register(self, id, factory, *args, **kw):
        log.debug('%s: registering %r -> %s(*%r, **%r)', self.__class__.__name__, id, factory, args, kw)
        assert id not in self._registry, repr(id)  # Duplicate id
        self._registry[id] = self._Rec(factory, args, kw)

    def is_registered(self, id):
        return id in self._registry

    def _resolve(self, id):
        assert id in self._registry, repr(id)  # Unknown id
        return self._registry[id]


class PieceRegistry(Registry):

    def __init__(self, produce_name, types):
        super().__init__()
        self._produce_name = produce_name
        self._types = types

    @property
    def produce_name(self):
        return self._produce_name

    def register(self, t, factory, *args, **kw):
        assert isinstance(t, Type), repr(t)
        assert t.full_name, repr(t)  # type must have a name
        super().register(tuple(t.full_name), factory, *args, **kw)

    def resolve(self, piece):
        assert isinstance(piece, href_types.piece), repr(piece)
        t = self._types.resolve(piece.full_type_name)
        object = packet_coders.decode(piece.encoding, piece.encoded_object, t)
        rec = self._resolve(tuple(piece.full_type_name))
        log.info('producing %s for %s using %s(%s, %s) for object %r',
                     self._produce_name, '.'.join(piece.full_type_name), rec.factory, rec.args, rec.kw, object)
        return rec.factory(object, *rec.args, **rec.kw)


class PieceResolver(object):

    def __init__(self, ref_resolver, piece_registry):
        self._ref_resolver = ref_resolver
        self._piece_registry = piece_registry

    def resolve(self, ref):
        assert isinstance(ref, bytes), repr(ref)
        piece = self._ref_resolver.resolve_ref(ref)
        produce = self._piece_registry.resolve(piece)
        assert produce, repr(produce)
        log.debug('piece resolved to %s %r', self._piece_registry.produce_name, produce)
        return produce
