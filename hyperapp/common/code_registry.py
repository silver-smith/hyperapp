import inspect
import logging
from collections import namedtuple

from .htypes import ref_t
from .htypes.deduce_value_type import deduce_value_type
from .visual_rep import pprint

_log = logging.getLogger(__name__)


class CodeRegistry:

    _Rec = namedtuple('_Rec', 'factory args kw')

    def __init__(self, produce_name, ref_resolver, types):
        super().__init__()
        self._produce_name = produce_name
        self._ref_resolver = ref_resolver
        self._types = types
        self._registry = {}  # t -> _Rec

    def register_actor(self, t, factory, *args, **kw):
        assert not inspect.iscoroutinefunction(factory), f"Use client CodeRegistry for async factories: {factory!r}"
        _log.info('Register %s: %s -> %s(*%r, **%r)', self._produce_name, t, factory, args, kw)
        assert t not in self._registry, repr(t)  # duplicate
        self._registry[t] = self._Rec(factory, args, kw)

    def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = self._ref_resolver.resolve_ref(ref)
        decoded_capsule = self._types.decode_capsule(capsule)
        return self._animate(decoded_capsule.t, decoded_capsule.value, args, kw)

    def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return self._animate(t, piece, args, kw)

    def _animate(self, t, piece, args, kw):
        # pprint(piece, t=t, logger=_log.info, title=f"Producing {self._produce_name} for {piece} of type {t}")
        rec = self._registry.get(t)
        if not rec:
            raise RuntimeError(f"No code is registered for {self._produce_name}: {t} {piece}")
        _log.debug('Producing %s for %s of type %s using %s(%s/%s, %s/%s)',
                   self._produce_name, piece, t, rec.factory, rec.args, args, rec.kw, kw)
        actor = rec.factory(piece, *args, *rec.args, **kw, **rec.kw)
        _log.info('%s: %s of type %s is resolved to %s', self._produce_name, piece, t, actor)
        return actor
