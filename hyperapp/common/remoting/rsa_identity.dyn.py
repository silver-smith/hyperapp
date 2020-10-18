from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from hyperapp.common.module import Module

from . import htypes


RSA_KEY_SIZE_SAFE = 4096  # Key size used when generating new identities. Slow.
RSA_KEY_SIZE_FAST = 1024  # Used for testing only.


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


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.identity_registry.register_actor(htypes.rsa_identity.rsa_identity, RsaIdentity.from_piece)
