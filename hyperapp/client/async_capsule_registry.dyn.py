import logging

from hyperapp.common.htypes import Type, ref_t, capsule_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.ref import ref_repr
from hyperapp.common.visual_rep import pprint
from hyperapp.common.registry import UnknownRegistryIdError
from hyperapp.common.capsule_registry import CapsuleRegistry
from hyperapp.client.async_registry import run_awaitable_factory

log = logging.getLogger(__name__)


class AsyncCapsuleRegistry(CapsuleRegistry):

    async def resolve_capsule_async(self, capsule, *args, **kw):
        assert isinstance(capsule, capsule_t), repr(capsule)
        t = self._type_resolver.resolve(capsule.type_ref)
        object = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        return (await self._resolve_object_async(capsule.type_ref, t, object, args, kw))

    async def resolve_async(self, object, *args, **kw):
        t = deduce_value_type(object)
        type_ref = self._type_resolver.reverse_resolve(t)
        return (await self._resolve_object_async(type_ref, t, object, args, kw))

    async def _resolve_object_async(self, type_ref, t, object, args, kw):
        pprint(object, t=t, title='Producing %s for %s of type %s' % (self._produce_name, object, ref_repr(type_ref)))
        try:
            rec = self._resolve(type_ref)
        except UnknownRegistryIdError as x:
            raise RuntimeError("No resolver is registered for {}: {} {}".format(self._produce_name, ref_repr(type_ref), object))
        log.info('Producing %s for %s of type %s using %s(%s/%s, %s/%s) for object %r',
                 self._produce_name, object, ref_repr(type_ref), rec.factory, rec.args, args, rec.kw, kw, object)
        return (await run_awaitable_factory(rec.factory, object, *(*rec.args, *args), **{**rec.kw, **kw}))


class AsyncCapsuleResolver(object):

    def __init__(self, async_ref_resolver, async_capsule_registry):
        self._async_ref_resolver = async_ref_resolver
        self._async_capsule_registry = async_capsule_registry

    async def resolve(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_ref_resolver.resolve_ref(ref)
        produce = await self._async_capsule_registry.resolve_capsule_async(capsule, *args, **kw)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._async_capsule_registry.produce_name, produce)
        return produce
