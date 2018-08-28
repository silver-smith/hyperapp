# registry for transient references

import logging

from .interface import hyper_ref as href_types
from .htypes import deduce_value_type
from .ref import ref_repr, make_capsule, make_ref
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):

    def __init__(self):
        self._registry = {}  # ref -> capsule

    def register_capsule(self, capsule):
        assert isinstance(capsule, href_types.capsule), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule %s', ref_repr(ref), capsule)
        existing_capsule = self._registry.get(ref)
        if existing_capsule:
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        self._registry[ref] = capsule
        return ref

    def register_object(self, object, t=None):
        t = t or deduce_value_type(object)
        capsule = make_capsule(t, object)
        return self.register_capsule(capsule)
        log.debug('Registered ref for %s: %s', '.'.join(t.full_name), ref_repr(ref))
        return ref

    def resolve_ref(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = ref_registry = RefRegistry()
        services.ref_resolver.add_source(ref_registry)
