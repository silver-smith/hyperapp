import codecs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from .htypes import ref_t, capsule_t, ref_repr
from .htypes.packet_coders import packet_coders


DEFAULT_HASH_ALGORITHM = 'sha512'
BUNDLE_ENCODING = 'json'


def phony_ref(ref_id):
    return ref_t('phony', ref_id.encode())


def make_ref(capsule):
    assert isinstance(capsule, capsule_t)
    # use same encoding for capsule as for object
    encoded_capsule = packet_coders.encode(capsule.encoding, capsule)
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(encoded_capsule)
    hash = digest.finalize()
    return ref_t(DEFAULT_HASH_ALGORITHM, hash)
