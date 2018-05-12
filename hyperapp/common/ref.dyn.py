import codecs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from ..common.interface import hyper_ref as href_types
from ..common.htypes import Type
from ..common.packet_coders import packet_coders


DEFAULT_ENCODING = 'cdr'
DEFAULT_HASH_ALGORITHM = 'sha512'
MAX_REF_REPR_LEN = 60
BUNDLE_ENCODING = 'json'


def ref_repr(ref):
    hex = str(codecs.encode(ref, 'hex'))
    if len(hex) > MAX_REF_REPR_LEN:
        return hex[:MAX_REF_REPR_LEN] + '...'
    else:
        return hex

def make_capsule(t, object):
    assert isinstance(t, Type), repr(t)
    assert isinstance(object, t), repr((t, object))
    encoding = DEFAULT_ENCODING
    encoded_object = packet_coders.encode(encoding, object, t)
    return href_types.capsule(t.full_name, DEFAULT_HASH_ALGORITHM, encoding, encoded_object)

def make_ref(capsule):
    assert isinstance(capsule, href_types.capsule)
    assert capsule.hash_algorithm == DEFAULT_HASH_ALGORITHM, repr(capsule.hash_algorithm)
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(capsule.encoded_object)
    return digest.finalize()

def make_object_ref(t, object):
    capsule = make_capsule(t, object)
    return make_ref(capsule)

def decode_object(t, capsule):
    assert t.full_name == capsule.full_type_name
    return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)

def encode_bundle(bundle):
    return packet_coders.encode(BUNDLE_ENCODING, bundle, href_types.bundle)

def decode_bundle(encoded_bundle):
    return packet_coders.decode(BUNDLE_ENCODING, encoded_bundle, href_types.bundle)
