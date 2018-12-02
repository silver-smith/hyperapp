import logging

from .util import full_type_name_to_str
from .htypes import Type, ref_t, capsule_t
from .htypes.packet_coders import packet_coders
from .ref import ref_repr
from .visual_rep import pprint
from .registry import Registry

log = logging.getLogger(__name__)


class CapsuleRegistry(Registry):

    def __init__(self, produce_name, type_registry):
        super().__init__()
        self._produce_name = produce_name
        self._type_registry = type_registry

    @property
    def produce_name(self):
        return self._produce_name

    def id_to_str(self, id):
        return ref_repr(id)

    def register_type_ref(self, ref, factory, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        super().register(ref, factory, *args, **kw)
        
    def resolve(self, ref, capsule, *args, **kw):
        assert isinstance(capsule, capsule_t), repr(capsule)
        t = self._type_registry.resolve(capsule.type_ref)
        object = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        pprint(object, t=t, title='Producing %s for capsule %s type %s'
               % (self._produce_name, ref_repr(ref), ref_repr(capsule.type_ref)))
        rec = self._resolve(ref)
        log.info('producing %s for %s of %s using %s(%s/%s, %s/%s) for object %r',
                 self._produce_name, ref_repr(ref), ref_repf(capsule.type_ref),
                 rec.factory, rec.args, args, rec.kw, kw, object)
        return rec.factory(ref, object, *(rec.args + args), **dict(rec.kw, **kw))


class CapsuleResolver(object):

    def __init__(self, ref_resolver, capsule_registry):
        self._ref_resolver = ref_resolver
        self._capsule_registry = capsule_registry

    def resolve(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = self._ref_resolver.resolve_ref(ref)
        assert capsule, 'Unknown ref: %s' % ref_repr(ref)
        produce = self._capsule_registry.resolve(ref, capsule, *args, **kw)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._capsule_registry.produce_name, produce)
        return produce
