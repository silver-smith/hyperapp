import logging

from .htypes import (
    Type,
    ref_t,
    builtin_ref_t,
    meta_ref_t,
    capsule_t,
    make_meta_type_registry,
    TypeRefResolver,
    )
from .htypes.deduce_value_type import deduce_value_type
from .htypes.packet_coders import packet_coders
from .ref import phony_ref, ref_repr
from .visual_rep import pprint
from .capsule_registry import CapsuleRegistry, CapsuleResolver

log = logging.getLogger(__name__)


DEFAULT_CAPSULE_ENCODING = 'cdr'


class UnexpectedTypeError(RuntimeError):

    def __init__(self, expected_type, actual_type):
        super().__init__("Capsule has unexpected type: expected is %r, actual is %r", expected_type, actual_type)


class _TypeRefResolver(TypeRefResolver):

    def __init__(self, type_resolver):
        self._type_resolver = type_resolver

    def resolve(self, type_ref, name=None):
        return self._type_resolver.resolve(type_ref.ref)


class TypeResolver(object):

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._type_capsule_registry = capsule_registry = CapsuleRegistry('type', self)
        self._type_capsule_resolver = type_capsule_resolver = CapsuleResolver(ref_resolver, capsule_registry)
        self._type_ref_resolver = _TypeRefResolver(self)
        self._meta_type_registry = make_meta_type_registry()
        self._ref2type_cache = {}  # we should resolve same ref to same instance, not a duplicate
        self._type2ref = {}  # reverse registry
        self._builtin_name_to_type = {}
        self._add_phony_refs()
        capsule_registry.register_type(builtin_ref_t, self._resolve_builtin_ref)
        capsule_registry.register_type(meta_ref_t, self._resolve_meta_ref)

    def _add_phony_refs(self):
        for t, ref_id in [
                (builtin_ref_t, 'BUILTIN_REF'),
                (meta_ref_t, 'META_REF'),
                ]:
            ref = phony_ref(ref_id)
            self._type2ref[t] = ref
            self._ref2type_cache[ref] = t

    def resolve(self, type_ref):
        t = self._ref2type_cache.get(type_ref)
        if t:
            log.info('Resolve type %s -> (cached) %s', ref_repr(type_ref), t)
            return t
        t = self._type_capsule_resolver.resolve(type_ref)
        self._ref2type_cache[type_ref] = t
        self._type2ref[t] = type_ref
        log.info('Resolve type %s -> %s', ref_repr(type_ref), t)
        return t

    def reverse_resolve(self, t):
        return self._type2ref[t]

    def _resolve_meta_ref(self, ref, meta_ref, name=None):
        return self._meta_type_registry.resolve(self._type_ref_resolver, meta_ref.type, meta_ref.name)

    def _resolve_builtin_ref(self, ref, builtin_ref, name=None):
        return self._ref2type_cache[ref]  # must be registered using register_builtin_type

    def make_capsule(self, object, t=None):
        t = t or deduce_value_type(object)
        assert isinstance(t, Type), repr(t)
        assert isinstance(object, t), repr((t, object))
        encoding = DEFAULT_CAPSULE_ENCODING
        encoded_object = packet_coders.encode(encoding, object, t)
        type_ref = self.reverse_resolve(t)
        pprint(object, t=t, title='Making capsule of type %s/%s' % (ref_repr(type_ref), t))
        return capsule_t(type_ref, encoding, encoded_object)

    def decode_capsule(self, capsule, expected_type=None):
        t = self.resolve(capsule.type_ref)
        if expected_type and t is not expected_type:
            raise UnexpectedTypeError(expected_type, t)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)

    def decode_object(self, t, capsule):
        type_ref = self.reverse_resolve(t)
        assert type_ref == capsule.type_ref
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)

    def register_builtin_type(self, ref_registry, t):
        assert t not in self._type2ref, repr(t)
        type_rec = builtin_ref_t(t.name)
        type_ref = ref_registry.register_object(type_rec)
        self._type2ref[t] = type_ref
        self._ref2type_cache[type_ref] = t
        self._builtin_name_to_type[t.name] = t

    @property
    def builtin_type_by_name(self):
        return self._builtin_name_to_type

    def resolve_ref_to_data(self, ref, expected_type=None):
        capsule = self._ref_resolver.resolve_ref(ref)
        assert capsule is not None, 'Unknown ref: %s' % ref_repr(ref)
        return self.decode_capsule(capsule, expected_type)
