from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes


RSA_KEY_SIZE_SAFE = 4096  # Key size used when generating new identities. Slow.
RSA_KEY_SIZE_FAST = 1024  # Used for testing only.
BUNDLE_ENCODING = 'cdr'


class RsaIdentity:

    @classmethod
    def generate(cls, fast=False):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE_FAST if fast else RSA_KEY_SIZE_SAFE,
            backend=default_backend()
        )
        return cls(private_key)

    @classmethod
    def from_piece(cls, piece):
        private_key = serialization.load_pem_private_key(piece.private_key_pem, password=None, backend=default_backend())
        return cls(private_key)

    def __init__(self, private_key: rsa.RSAPrivateKeyWithSerialization):
        self._private_key = private_key

    @property
    def piece(self):
        private_key_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            )
        return htypes.rsa_identity.rsa_identity(private_key_pem)

    @property
    def peer(self):
        return RsaPeer(self._private_key.public_key())

    def sign(self, data):
        hash_algorithm = hashes.SHA256()
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hash_algorithm,
            )
        return htypes.rsa_identity.rsa_signature(
            hash_algorithm='sha256',
            padding='pss',
            signature=signature,
            )


class RsaPeer:

    @classmethod
    def from_piece(cls, piece):
        public_key = serialization.load_pem_public_key(piece.public_key_pem, backend=default_backend())
        return cls(public_key)

    def __init__(self, public_key: rsa.RSAPublicKey):
        self._public_key = public_key

    @property
    def piece(self):
        return htypes.rsa_identity.rsa_peer(self._public_key_pem)

    @property
    def _public_key_pem(self):
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

    def make_parcel(self, bundle, sender_identity, ref_registry):
        plain_data = packet_coders.encode(BUNDLE_ENCODING, bundle)
        hash_alg = hashes.SHA1()
        cipher_data = self._public_key.encrypt(
            plain_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_alg),
                algorithm=hash_alg,
                label=None))
        signature = sender_identity.sign(cipher_data)
        signature_ref = ref_registry.register_object(signature)
        return htypes.rsa_identity.rsa_parcel(
            peer_public_key_pem=self._public_key_pem,
            encrypted_bundle=cipher_data,
            sender_signature_ref=signature_ref,
            )

    
class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.identity_registry.register_actor(htypes.rsa_identity.rsa_identity, RsaIdentity.from_piece)
        services.peer_registry.register_actor(htypes.rsa_identity.rsa_peer, RsaPeer.from_piece)
