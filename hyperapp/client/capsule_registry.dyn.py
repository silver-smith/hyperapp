import logging

from ..common.interface import hyper_ref as href_types
from ..common.util import full_type_name_to_str
from ..common.htypes import Type, ref_t
from ..common.htypes.packet_coders import packet_coders
from ..common.ref import ref_repr
from ..common.visual_rep import pprint
from .registry import Registry

log = logging.getLogger(__name__)


class CapsuleRegistry(Registry):

    def __init__(self, produce_name, types):
        super().__init__()
        self._produce_name = produce_name
        self._types = types

    @property
    def produce_name(self):
        return self._produce_name

    def id_to_str(self, id):
        return full_type_name_to_str(id)

    def register(self, t, factory, *args, **kw):
        assert isinstance(t, Type), repr(t)
        assert t.full_name, repr(t)  # type must have a name
        super().register(tuple(t.full_name), factory, *args, **kw)
        
    async def resolve(self, ref, capsule):
        assert isinstance(capsule, href_types.capsule), repr(capsule)
        t = self._types.resolve(capsule.full_type_name)
        object = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        pprint(object, t=t, title='Producing %s for capsule %s %s' % (self._produce_name, ref_repr(ref), full_type_name_to_str(capsule.full_type_name)))
        rec = self._resolve(tuple(capsule.full_type_name))
        log.info('producing %s for %s using %s(%s, %s) for object %r',
                     self._produce_name, full_type_name_to_str(capsule.full_type_name), rec.factory, rec.args, rec.kw, object)
        return (await self._run_awaitable_factory(rec.factory, ref, object, *rec.args, **rec.kw))


class CapsuleResolver(object):

    def __init__(self, async_ref_resolver, capsule_registry):
        self._async_ref_resolver = async_ref_resolver
        self._capsule_registry = capsule_registry

    async def resolve(self, ref):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_ref_resolver.resolve_ref(ref)
        produce = await self._capsule_registry.resolve(ref, capsule)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._capsule_registry.produce_name, produce)
        return produce
