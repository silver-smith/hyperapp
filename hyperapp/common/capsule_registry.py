import logging

from .htypes import Type, ref_t, capsule_t
from .htypes.deduce_value_type import deduce_value_type
from .htypes.packet_coders import packet_coders
from .ref import ref_repr
from .visual_rep import pprint
from .registry import UnknownRegistryIdError, RegistryBase

log = logging.getLogger(__name__)


class CapsuleRegistry(RegistryBase):

    def __init__(self, produce_name, type_resolver):
        super().__init__()
        self._produce_name = produce_name
        self._type_resolver = type_resolver

    @property
    def produce_name(self):
        return self._produce_name

    def id_to_str(self, id):
        return ref_repr(id)

    def register_type(self, t, factory, *args, **kw):
        type_ref = self._type_resolver.reverse_resolve(t)
        self.register_type_ref(type_ref, factory, *args, **kw)

    def register_type_ref(self, ref, factory, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        self._register(ref, factory, *args, **kw)
        
    def resolve_capsule(self, capsule, *args, **kw):
        assert isinstance(capsule, capsule_t), repr(capsule)
        t = self._type_resolver.resolve(capsule.type_ref)
        object = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        return self._resolve_object(capsule.type_ref, t, object, args, kw)

    def resolve(self, object, *args, **kw):
        t = deduce_value_type(object)
        type_ref = self._type_resolver.reverse_resolve(t)
        return self._resolve_object(type_ref, t, object, args, kw)

    def _resolve_object(self, type_ref, t, object, args, kw):
        pprint(object, t=t, title='Producing %s for %s of type %s'
               % (self._produce_name, object, ref_repr(type_ref)))
        try:
            rec = self._resolve(type_ref)
        except UnknownRegistryIdError as x:
            raise RuntimeError("No resolver is registered for {}: {} {}".format(self._produce_name, ref_repr(type_ref), object))
        log.info('Producing %s for %s of type %s using %s(%s/%s, %s/%s) for object %r',
                 self._produce_name, object, ref_repr(type_ref),
                 rec.factory, rec.args, args, rec.kw, kw, object)
        return rec.factory(object, *(*rec.args, *args), **{**rec.kw, **kw})


class CapsuleResolver(object):

    def __init__(self, ref_resolver, capsule_registry):
        self._ref_resolver = ref_resolver
        self._capsule_registry = capsule_registry

    def resolve(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = self._ref_resolver.resolve_ref(ref)
        assert capsule, 'Unknown ref: %s' % ref_repr(ref)
        produce = self._capsule_registry.resolve_capsule(capsule, *args, **kw)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._capsule_registry.produce_name, produce)
        return produce
