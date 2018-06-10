# registry for transient references

import logging

from .interface import hyper_ref as href_types
from .ref import ref_repr, make_capsule, make_ref
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):

    def __init__(self):
        self._registry = {}  # ref -> capsule

    def _register(self, capsule):
        assert isinstance(capsule, href_types.capsule), repr(capsule)
        ref = make_ref(capsule)
        log.debug('Registering ref %s for capsule %s', ref_repr(ref), capsule)
        existing_capsule = self._registry.get(ref)
        if existing_capsule:
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        self._registry[ref] = capsule
        return ref

    def register_object(self, t, object):
        capsule = make_capsule(t, object)
        return self._register(capsule)
        log.debug('Registered ref for %s: %s', '.'.join(t.full_name), ref_repr(ref))
        return ref

    def register_capsule_list(self, capsule_list):
        for capsule in capsule_list:
            self._register(capsule)

    def register_bundle(self, bundle):
        self.register_capsule_list(bundle.capsule_list)

    def resolve_ref(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = ref_registry = RefRegistry()
        services.ref_resolver.add_source(ref_registry)
