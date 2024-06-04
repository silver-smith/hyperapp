from collections import namedtuple
import codecs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from .htypes import Type, ref_t, capsule_t, ref_repr
from .htypes.deduce_value_type import deduce_value_type
from .htypes.packet_coders import packet_coders


DEFAULT_HASH_ALGORITHM = 'sha512'
DEFAULT_CAPSULE_ENCODING = 'cdr'


DecodedCapsule = namedtuple('_DecodedCapsule', 'type_ref t value')


class UnexpectedTypeError(RuntimeError):

    def __init__(self, expected_type, actual_type):
        super().__init__("Capsule has unexpected type: expected is %r, actual is %r", expected_type, actual_type)


def hash_sha512(source_bytes):
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(source_bytes)
    return digest.finalize()


def make_ref(capsule):
    assert isinstance(capsule, capsule_t)
    # use same encoding for capsule as for object
    encoded_capsule = packet_coders.encode(capsule.encoding, capsule)
    hash = hash_sha512(encoded_capsule)
    return ref_t(DEFAULT_HASH_ALGORITHM, hash)


def make_capsule(mosaic, pyobj_creg, object, t=None):
    t = t or deduce_value_type(object)
    assert isinstance(t, Type), repr(t)
    assert isinstance(object, t), repr((t, object))
    encoding = DEFAULT_CAPSULE_ENCODING
    encoded_object = packet_coders.encode(encoding, object, t)
    type_piece = pyobj_creg.actor_to_piece(t)
    type_ref = mosaic.put(type_piece)
    return capsule_t(type_ref, encoding, encoded_object)


def decode_capsule(pyobj_creg, capsule, expected_type=None):
    t = pyobj_creg.invite(capsule.type_ref)
    if expected_type and t is not expected_type:
        raise UnexpectedTypeError(expected_type, t)
    value = packet_coders.decode(capsule.encoding, capsule.encoded_object, t)
    return DecodedCapsule(capsule.type_ref, t, value)
