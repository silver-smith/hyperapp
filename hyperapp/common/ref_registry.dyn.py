# registry for transient references

import logging

from .interface import hyper_ref as href_types
from .ref import ref_repr, make_referred, make_ref
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):

    def __init__(self):
        self._registry = {}  # ref -> referred

    def register_object(self, t, object):
        referred = make_referred(t, object)
        ref = make_ref(referred)
        assert ref not in self._registry  # already registered
        self._registry[ref] = referred
        log.debug('Registered ref for %s: %s', '.'.join(t.full_name), ref_repr(ref))
        return ref

    def resolve_ref(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = ref_registry = RefRegistry()
        services.ref_resolver.add_source(ref_registry)
