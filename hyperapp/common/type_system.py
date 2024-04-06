import logging

from .htypes import (
    builtin_mt,
    register_builtin_meta_types,
    register_meta_types,
    )
from .code_registry import CodeRegistry

_log = logging.getLogger(__name__)


class TypeSystem(object):

    def __init__(self):
        self._type_code_registry = None
        self._ref2type_cache = {}  # we should resolve same ref to same instance, not a duplicate
        self._type2ref = {}  # reverse registry

    def init(self, builtin_types, mosaic, web):
        self._type_code_registry = CodeRegistry(mosaic, web, self, None, None, 'type')

        builtin_types.register_builtin_mt(self, self._type_code_registry)
        register_builtin_meta_types(builtin_types, mosaic, self)
        register_meta_types(mosaic, self, self._type_code_registry)

    def resolve(self, type_ref):
        t = self._ref2type_cache.get(type_ref)
        if t:
            _log.debug('Resolve type %s -> (cached) (#%s) %r', type_ref, id(t), t)
            return t
        t = self._type_code_registry.invite(type_ref, self._type_code_registry, None, None)  # module_name==name==None
        self._ref2type_cache[type_ref] = t
        assert t not in self._type2ref, (type_ref, self._type2ref[t], t, self._ref2type_cache[self._type2ref[t]])
        self._type2ref[t] = type_ref
        _log.debug('Resolve type %s -> (#%s) %r', type_ref, id(t), t)
        return t

    def reverse_resolve(self, t):
        return self._type2ref[t]

    def add_to_cache(self, type_ref, t):
        assert t not in self._type2ref, repr(t)
        self._type2ref[t] = type_ref
        self._ref2type_cache[type_ref] = t
