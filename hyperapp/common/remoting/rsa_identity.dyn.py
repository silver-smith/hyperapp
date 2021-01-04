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
    def generate(cls, ref_registry, fast=False):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE_FAST if fast else RSA_KEY_SIZE_SAFE,
            backend=default_backend(),
        )
        return cls(ref_registry, private_key)

    @classmethod
    def from_piece(cls, piece, ref_registry):
        private_key = serialization.load_pem_private_key(piece.private_key_pem, password=None, backend=default_backend())
        return cls(ref_registry, private_key)

    def __init__(self, ref_registry, private_key: rsa.RSAPrivateKeyWithSerialization):
        self._ref_registry = ref_registry
        self._private_key = private_key

    @property
    def piece(self):
        private_key_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
            )
        return htypes.rsa_identity.rsa_identity(private_key_pem)

    @property
    def peer(self):
        return RsaPeer(self._ref_registry, self._private_key.public_key())

    def sign(self, data):
        hash_algorithm = hashes.SHA256()
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hash_algorithm,
            )
        return RsaSignature(
            signer=self.peer,
            hash_algorithm='sha256',
            padding='pss',
            signature=signature,
            )


class RsaPeer:

    @classmethod
    def from_piece(cls, piece, ref_registry):
        return cls.from_public_key_pem(ref_registry, piece.public_key_pem)

    @classmethod
    def from_public_key_pem(cls, ref_registry, public_key_pem):
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        return cls(ref_registry, public_key)

    def __init__(self, ref_registry, public_key: rsa.RSAPublicKey):
        self._ref_registry = ref_registry
        self._public_key = public_key

    @property
    def piece(self):
        return htypes.rsa_identity.rsa_peer(self.public_key_pem)

    @property
    def public_key_pem(self):
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

    def make_parcel(self, bundle, sender_identity):
        plain_data = packet_coders.encode(BUNDLE_ENCODING, bundle)
        hash_algorithm = hashes.SHA1()
        cipher_data = self._public_key.encrypt(
            plain_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_algorithm),
                algorithm=hash_algorithm,
                label=None,
                ))
        signature = sender_identity.sign(cipher_data)
        return RsaParcel(
            self._ref_registry,
            receiver=self,
            encrypted_bundle=cipher_data,
            signature=signature,
            )


class RsaSignature:

    @classmethod
    def from_piece(cls, piece, ref_registry):
        signer = RsaPeer.from_public_key_pem(ref_registry, piece.signer_public_key_pem)
        return cls(signer, piece.hash_algorithm, piece.padding, piece.signature)

    def __init__(self, signer, hash_algorithm, padding, signature):
        self._signer = signer
        self._hash_algorithm = hash_algorithm
        self._padding = padding
        self._signature = signature

    @property
    def piece(self):
        return htypes.rsa_identity.rsa_signature(
            signer_public_key_pem=self._signer.public_key_pem,
            hash_algorithm=self._hash_algorithm,
            padding=self._padding,
            signature=self._signature,
            )

    @property
    def signer(self):
        return self._signer


class RsaParcel:

    @classmethod
    def from_piece(cls, piece, ref_registry, signature_registry):
        signature = signature_registry.invite(piece.sender_signature_ref)
        receiver = RsaPeer.from_public_key_pem(ref_registry, piece.receiver_public_key_pem)
        return cls(ref_registry, receiver, piece.encrypted_bundle, signature)

    def __init__(self, ref_registry, receiver, encrypted_bundle, signature):
        self._ref_registry = ref_registry
        self._receiver = receiver
        self._encrypted_bundle = encrypted_bundle
        self._signature = signature

    @property
    def piece(self):
        signature_ref = self._ref_registry.distil(self._signature.piece)
        return htypes.rsa_identity.rsa_parcel(
            receiver_public_key_pem=self._receiver.public_key_pem,
            encrypted_bundle=self._encrypted_bundle,
            sender_signature_ref=signature_ref,
            )

    @property
    def receiver(self):
        return self._receiver

    @property
    def sender(self):
        return self._signature.signer


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._ref_registry = services.ref_registry
        services.identity_registry.register_actor(
            htypes.rsa_identity.rsa_identity, RsaIdentity.from_piece, services.ref_registry)
        services.peer_registry.register_actor(
            htypes.rsa_identity.rsa_peer, RsaPeer.from_piece, services.ref_registry)
        services.signature_registry.register_actor(
            htypes.rsa_identity.rsa_signature, RsaSignature.from_piece, services.ref_registry)
        services.parcel_registry.register_actor(
            htypes.rsa_identity.rsa_parcel, RsaParcel.from_piece, services.ref_registry, services.signature_registry)
        services.generate_rsa_identity = self.generate_identity

    def generate_identity(self, fast=False):
        return RsaIdentity.generate(self._ref_registry, fast)
