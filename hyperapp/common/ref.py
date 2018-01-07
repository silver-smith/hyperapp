import codecs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from ..common.htypes import Type
from ..common.interface import hyper_ref as href_types
from ..common.packet_coders import packet_coders


DEFAULT_ENCODING = 'cdr'
DEFAULT_HASH_ALGORITHM = 'sha512'
MAX_REF_REPR_LEN = 60


def ref_repr(ref):
    hex = str(codecs.encode(ref, 'hex'))
    if len(hex) > MAX_REF_REPR_LEN:
        return hex[:MAX_REF_REPR_LEN] + '...'
    else:
        return hex

def make_referred(t, object):
    assert isinstance(t, Type), repr(t)
    assert isinstance(object, t), repr((t, object))
    encoding = DEFAULT_ENCODING
    encoded_object = packet_coders.encode(encoding, object, t)
    return href_types.referred(t.full_name, DEFAULT_HASH_ALGORITHM, encoding, encoded_object)

def make_ref(referred):
    assert isinstance(referred, href_types.referred)
    assert referred.hash_algorithm == DEFAULT_HASH_ALGORITHM, repr(referred.hash_algorithm)
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(referred.encoded_object)
    return digest.finalize()
