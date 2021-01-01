import logging
from collections import namedtuple

from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.visual_rep import pprint
from hyperapp.client.async_registry import run_awaitable_factory

_log = logging.getLogger(__name__)


class CodeRegistry:

    _Rec = namedtuple('_Rec', 'factory args kw')

    def __init__(self, produce_name, async_ref_resolver, types):
        super().__init__()
        self._produce_name = produce_name
        self._async_ref_resolver = async_ref_resolver
        self._types = types
        self._registry = {}  # t -> _Rec

    def register_actor(self, t, factory, *args, **kw):
        _log.info('Register %s: %s -> %s(*%r, **%r)', self._produce_name, t, factory, args, kw)
        assert t not in self._registry, repr(t)  # duplicate
        self._registry[t] = self._Rec(factory, args, kw)

    async def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_ref_resolver.resolve_ref(ref)
        decoded_capsule = self._types.decode_capsule(capsule)
        return (await self._animate(decoded_capsule.t, decoded_capsule.value, args, kw))

    async def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return (await self._animate(t, piece, args, kw))

    async def _animate(self, t, piece, args, kw):
        # pprint(piece, t=t, logger=_log.info, title=f"Producing {self._produce_name} for {piece} of type {t}")
        rec = self._registry.get(t)
        if not rec:
            raise RuntimeError(f"No code is registered for {self._produce_name}: {t} {piece}")
        _log.debug('Producing %s for %s of type %s using %s(%s/%s, %s/%s)',
                   self._produce_name, piece, t, rec.factory, rec.args, args, rec.kw, kw)
        actor = await run_awaitable_factory(rec.factory, piece, *args, *rec.args, **kw, **rec.kw)
        _log.info('%s: %s of type %s is resolved to %s', self._produce_name, piece, t, actor)
        return actor
