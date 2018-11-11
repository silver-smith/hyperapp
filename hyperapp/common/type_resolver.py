import logging

from .htypes import (
    builtin_ref_t,
    meta_ref_t,
    make_meta_type_registry,
    TypeRefResolver,
    )
from .ref import ref_repr
from .capsule_registry import CapsuleRegistry, CapsuleResolver

log = logging.getLogger(__name__)


class _TypeRefResolver(TypeRefResolver):

    def __init__(self, type_resolver):
        self._type_resolver = type_resolver

    def resolve(self, type_ref, name):
        return self._type_resolver.resolve(type_ref.ref)


class TypeResolver(object):

    def __init__(self, types, builtin_types_registry, ref_resolver):
        self._types = types
        self._builtin_types_registry = builtin_types_registry
        self._ref_resolver = ref_resolver
        self._type_capsule_registry = capsule_registry = CapsuleRegistry('type', types)
        self._type_capsule_resolver = type_capsule_resolver = CapsuleResolver(ref_resolver, capsule_registry)
        self._type_ref_resolver = _TypeRefResolver(self)
        self._meta_type_registry = make_meta_type_registry()
        self._ref2type_cache = {}  # we should resolve same ref to same instance, not a duplicate
        capsule_registry.register(meta_ref_t, self._resolve_meta_ref)
        capsule_registry.register(builtin_ref_t, self._resolve_builtin_ref)

    def resolve(self, type_ref):
        t = self._ref2type_cache.get(type_ref)
        if t:
            log.info('Resolve type %s -> (cached) %s', ref_repr(type_ref), t)
            return t
        t = self._type_capsule_resolver.resolve(type_ref)
        self._ref2type_cache[type_ref] = t
        log.info('Resolve type %s -> %s', ref_repr(type_ref), t)
        return t

    def _resolve_meta_ref(self, ref, meta_ref, name=None):
        return self._meta_type_registry.resolve(self._type_ref_resolver, meta_ref.type, [meta_ref.name])

    def _resolve_builtin_ref(self, ref, builtin_ref, name=None):
        return self._builtin_types_registry[builtin_ref.full_name]
