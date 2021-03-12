from collections import namedtuple
import logging

from .htypes import (
    builtin_mt,
    register_builtin_meta_types,
    register_meta_types,
    )
from .ref import ref_repr
from .code_registry import CodeRegistry

_log = logging.getLogger(__name__)


_RegisteredType = namedtuple('_RegisteredType', 't ref')


class TypeSystem(object):

    def __init__(self):
        self._mosaic = None
        self._type_code_registry = None
        self._ref2type_cache = {}  # we should resolve same ref to same instance, not a duplicate
        self._type2ref = {}  # reverse registry

    def init(self, builtin_types, mosaic):
        self._mosaic = mosaic
        self._type_code_registry = CodeRegistry('type', mosaic, self)

        builtin_types.register_builtin_mt(self, self._type_code_registry)
        register_builtin_meta_types(builtin_types, mosaic, self)
        register_meta_types(self._mosaic, self, self._type_code_registry)

    def resolve(self, type_ref):
        t = self._ref2type_cache.get(type_ref)
        if t:
            _log.debug('Resolve type %s -> (cached) %s', ref_repr(type_ref), t)
            return t
        t = self._type_code_registry.invite(type_ref, self._type_code_registry, None)  # name=None
        self._ref2type_cache[type_ref] = t
        self._type2ref[t] = type_ref
        _log.debug('Resolve type %s -> %s', ref_repr(type_ref), t)
        return t

    def reverse_resolve(self, t):
        return self._type2ref[t]

    def add_to_cache(self, type_ref, t):
        assert t not in self._type2ref, repr(t)
        self._type2ref[t] = type_ref
        self._ref2type_cache[type_ref] = t

    def register_type(self, type_rec):
        type_ref = self._mosaic.put(type_rec)
        t = self.resolve(type_ref)
        _log.debug("Registered type: %s -> %s", ref_repr(type_ref), t)
        return _RegisteredType(t, type_ref)

    def get_builtin_type_ref(self, name):
        t = self._builtin_name_to_type[name]
        return self.reverse_resolve(t)
