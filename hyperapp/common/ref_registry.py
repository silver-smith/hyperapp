# reference registry: map refs to capsules

import logging

from .htypes import capsule_t
from .util import full_type_name_to_str
from .htypes.deduce_value_type import deduce_value_type
from .ref import ref_repr, make_capsule, decode_capsule, make_ref
from .visual_rep import pprint

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):

    def __init__(self, types):
        self._types = types
        self._registry = {}  # ref -> capsule

    def register_capsule(self, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        ref = make_ref(capsule)
        log.info('Registering ref %s for capsule %s', ref_repr(ref), full_type_name_to_str(capsule.full_type_name))
        existing_capsule = self._registry.get(ref)
        if existing_capsule:
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        self._registry[ref] = capsule
        pprint(decode_capsule(self._types, capsule), indent=1, logger=log.debug)
        return ref

    def register_object(self, object, t=None):
        t = t or deduce_value_type(object)
        capsule = make_capsule(object, t)
        return self.register_capsule(capsule)
        log.debug('Registered ref %s for object %s', ref_repr(ref), full_type_name_to_str(t.full_name))
        return ref

    def resolve_ref(self, ref):
        return self._registry.get(ref)
