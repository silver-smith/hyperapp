from collections import namedtuple
import logging

from .htypes import (
    Type,
    ref_t,
    builtin_mt,
    capsule_t,
    register_builtin_meta_types,
    register_meta_types,
    )
from .htypes.deduce_value_type import deduce_value_type
from .htypes.packet_coders import packet_coders
from .ref import phony_ref, ref_repr
from .visual_rep import pprint
from .code_registry import CodeRegistry

_log = logging.getLogger(__name__)


DEFAULT_CAPSULE_ENCODING = 'cdr'


class UnexpectedTypeError(RuntimeError):

    def __init__(self, expected_type, actual_type):
        super().__init__("Capsule has unexpected type: expected is %r, actual is %r", expected_type, actual_type)


_DecodedCapsule = namedtuple('_DecodedCapsule', 'type_ref t value')
_RegisteredType = namedtuple('_RegisteredType', 't ref')


class TypeSystem(object):

    def __init__(self):
        self._mosaic = None
        self._type_code_registry = None
        self._ref2type_cache = {}  # we should resolve same ref to same instance, not a duplicate
        self._type2ref = {}  # reverse registry
        self._builtin_name_to_type = {}

    def init_mosaic(self, mosaic):
        self._mosaic = mosaic
        self._type_code_registry = CodeRegistry('type', mosaic, self)
        self._type_code_registry.register_actor(ref_t, self._ref_from_piece)
        self._type_code_registry.register_actor(builtin_mt, self._builtin_from_piece)
        # Register builtin_mt with phony ref - can not be registered as usual because of dependency loop.
        builtin_ref = phony_ref('BUILTIN_REF')
        self._type2ref[builtin_mt] = builtin_ref
        self._ref2type_cache[builtin_ref] = builtin_mt
        #
        register_builtin_meta_types(self)
        register_meta_types(self._mosaic, self, self._type_code_registry)

    def _ref_from_piece(self, piece, type_code_registry, name):
        return self._resolve(piece, name)

    def _builtin_from_piece(self, piece, type_code_registry, name):
        return self._builtin_name_to_type[piece.name]  # must be registered using register_builtin_type

    def resolve(self, type_ref):
        return self._resolve(type_ref, name=None)

    def _resolve(self, type_ref, name):
        t = self._ref2type_cache.get(type_ref)
        if t:
            _log.debug('Resolve type %s -> (cached) %s', ref_repr(type_ref), t)
            return t
        t = self._type_code_registry.invite(type_ref, self._type_code_registry, name)
        self._ref2type_cache[type_ref] = t
        self._type2ref[t] = type_ref
        _log.debug('Resolve type %s -> %s', ref_repr(type_ref), t)
        return t

    def reverse_resolve(self, t):
        return self._type2ref[t]

    def make_capsule(self, object, t=None):
        t = t or deduce_value_type(object)
        assert isinstance(t, Type), repr(t)
        assert isinstance(object, t), repr((t, object))
        encoding = DEFAULT_CAPSULE_ENCODING
        encoded_object = packet_coders.encode(encoding, object, t)
        type_ref = self.reverse_resolve(t)
        # pprint(object, t=t, title='Making capsule of type %s/%s' % (ref_repr(type_ref), t))
        return capsule_t(type_ref, encoding, encoded_object)

    def decode_capsule(self, capsule, expected_type=None):
        t = self.resolve(capsule.type_ref)
        if expected_type and t is not expected_type:
            raise UnexpectedTypeError(expected_type, t)
        value = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
        return _DecodedCapsule(capsule.type_ref, t, value)

    def decode_object(self, t, capsule):
        type_ref = self.reverse_resolve(t)
        assert type_ref == capsule.type_ref
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)

    def register_builtin_type(self, t):
        assert t not in self._type2ref, repr(t)
        piece = builtin_mt(t.name)
        type_ref = self._mosaic.put(piece)
        self._type2ref[t] = type_ref
        self._ref2type_cache[type_ref] = t
        self._builtin_name_to_type[t.name] = t
        _log.debug("Registered builtin type %s: %s", t, ref_repr(type_ref))

    def register_type(self, type_rec):
        type_ref = self._mosaic.put(type_rec)
        t = self.resolve(type_ref)
        _log.debug("Registered type: %s -> %s", ref_repr(type_ref), t)
        return _RegisteredType(t, type_ref)

    @property
    def builtin_type_by_name(self):
        return self._builtin_name_to_type

    def get_builtin_type_ref(self, name):
        t = self._builtin_name_to_type[name]
        return self.reverse_resolve(t)

    def resolve_ref(self, ref, expected_type=None) -> _DecodedCapsule:
        capsule = self._mosaic.get(ref)
        assert capsule is not None, 'Unknown ref: %s' % ref_repr(ref)
        return self.decode_capsule(capsule, expected_type)
