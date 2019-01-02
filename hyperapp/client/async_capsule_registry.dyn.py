import logging

from hyperapp.common.util import full_type_name_to_str
from hyperapp.common.htypes import Type, ref_t, capsule_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.ref import ref_repr
from hyperapp.common.visual_rep import pprint
from hyperapp.common.visual_rep import CapsuleRegistry
from hyperapp.client.async_registry import run_awaitable_factory

log = logging.getLogger(__name__)


class AsyncCapsuleRegistry(CapsuleRegistry):

    async def resolve_async(self, ref, capsule, *args, **kw):
        rec = self._resolve_rec(ref, capsule)
        log.info('Producing %s for capsule %s of type %s using %s(%s/%s, %s/%s) for object %r',
                 self._produce_name, ref_repr(ref), ref_repr(capsule.type_ref),
                 rec.factory, rec.args, args, rec.kw, kw, object)
        return (await run_awaitable_factory(rec.factory, ref, object, *(rec.args + args), **dict(rec.kw, **kw)))


class AsyncCapsuleResolver(object):

    def __init__(self, async_ref_resolver, async_capsule_registry):
        self._async_ref_resolver = async_ref_resolver
        self._async_capsule_registry = async_capsule_registry

    async def resolve(self, ref):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_ref_resolver.resolve_ref(ref)
        produce = await self._async_capsule_registry.resolve(ref, capsule)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._async_capsule_registry.produce_name, produce)
        return produce
