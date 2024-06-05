from functools import cached_property

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    identity_registry,
    mark,
    mosaic,
    parcel_registry,
    peer_registry,
    signature_registry,
    )


RSA_KEY_SIZE_SAFE = 4096  # Key size used when generating new identities. Slow.
RSA_KEY_SIZE_FAST = 1024  # Used for testing only.
BUNDLE_ENCODING = 'cdr'


class RsaIdentity:

    @classmethod
    def generate(cls, fast=False):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE_FAST if fast else RSA_KEY_SIZE_SAFE,
            backend=default_backend(),
        )
        return cls(private_key)

    @classmethod
    def from_piece(cls, piece):
        private_key = serialization.load_pem_private_key(piece.private_key_pem, password=None, backend=default_backend())
        return cls(private_key)

    def __init__(self, private_key: rsa.RSAPrivateKeyWithSerialization):
        self._private_key = private_key

    def __repr__(self):
        pem_tail = self.peer.public_key_pem.splitlines()[-2][-10:].decode()
        return f"<RsaIdentity {pem_tail}>"

    @property
    def piece(self):
        private_key_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
            )
        return htypes.rsa_identity.rsa_identity(private_key_pem)

    @cached_property
    def peer(self):
        return RsaPeer(self._private_key.public_key())

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

    def decrypt_parcel(self, parcel):
        hash_algorithm = hashes.SHA256()
        fernet_key = self._private_key.decrypt(
            parcel.encrypted_fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_algorithm),
                algorithm=hash_algorithm,
                label=None,
                ))
        fernet = Fernet(fernet_key)
        bundle_cdr = fernet.decrypt(parcel.encrypted_bundle)
        return packet_coders.decode(BUNDLE_ENCODING, bundle_cdr, bundle_t)


class RsaPeer:

    @classmethod
    def from_piece(cls, piece):
        return cls.from_public_key_pem(piece.public_key_pem)

    @classmethod
    def from_public_key_pem(cls, public_key_pem):
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        return cls(public_key)

    def __init__(self, public_key: rsa.RSAPublicKey):
        self._public_key = public_key

    def __repr__(self):
        pem_tail = self.public_key_pem.splitlines()[-2][-10:].decode()
        return f"<RsaPeer {pem_tail}>"

    @property
    def piece(self):
        return htypes.rsa_identity.rsa_peer(self.public_key_pem)

    @cached_property
    def public_key_pem(self):
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

    def make_parcel(self, bundle, sender_identity):
        key = Fernet.generate_key()
        fernet = Fernet(key)
        bundle_cdr = packet_coders.encode(BUNDLE_ENCODING, bundle)
        encrypted_bundle = fernet.encrypt(bundle_cdr)
        hash_algorithm = hashes.SHA256()
        encrypted_key = self._public_key.encrypt(
            key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_algorithm),
                algorithm=hash_algorithm,
                label=None,
                ),
            )
        signature = sender_identity.sign(encrypted_bundle)
        return RsaParcel(
            receiver=self,
            encrypted_fernet_key=encrypted_key,
            encrypted_bundle=encrypted_bundle,
            signature=signature,
            )


class RsaSignature:

    @classmethod
    def from_piece(cls, piece):
        signer = RsaPeer.from_public_key_pem(piece.signer_public_key_pem)
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

    def verify(self, data):
        hash_algorithm = hashes.SHA256()
        self._signer._public_key.verify(
            self._signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH,
                ),
            hash_algorithm,
            )


class RsaParcel:

    @classmethod
    def from_piece(cls, piece):
        signature = signature_registry.invite(piece.sender_signature_ref)
        receiver = RsaPeer.from_public_key_pem(piece.receiver_public_key_pem)
        return cls(receiver, piece.encrypted_fernet_key, piece.encrypted_bundle, signature)

    def __init__(self, receiver, encrypted_fernet_key, encrypted_bundle, signature):
        self._receiver = receiver
        self._encrypted_fernet_key = encrypted_fernet_key
        self._encrypted_bundle = encrypted_bundle
        self._signature = signature

    def __repr__(self):
        return '<RsaParsel>'

    @property
    def piece(self):
        signature_ref = mosaic.put(self._signature.piece)
        return htypes.rsa_identity.rsa_parcel(
            receiver_public_key_pem=self._receiver.public_key_pem,
            encrypted_fernet_key=self._encrypted_fernet_key,
            encrypted_bundle=self._encrypted_bundle,
            sender_signature_ref=signature_ref,
            )

    @property
    def receiver(self):
        return self._receiver

    def verify(self):
        return self._signature.verify(self._encrypted_bundle)

    @property
    def sender(self):
        return self._signature.signer

    @property
    def encrypted_fernet_key(self):
        return self._encrypted_fernet_key

    @property
    def encrypted_bundle(self):
        return self._encrypted_bundle


@mark.service
def generate_rsa_identity():
    def _generate_rsa_identity(fast=False):
        return RsaIdentity.generate(fast)
    return _generate_rsa_identity


@identity_registry.actor(htypes.rsa_identity.rsa_identity)
def rsa_identity_from_piece(piece):
    return RsaIdentity.from_piece(piece)


@peer_registry.actor(htypes.rsa_identity.rsa_peer)
def rsa_peer_from_piece(piece):
    return RsaPeer.from_piece(piece)


@signature_registry.actor(htypes.rsa_identity.rsa_signature)
def rsa_signature_from_piece(piece):
    return RsaSignature.from_piece(piece)


@parcel_registry.actor(htypes.rsa_identity.rsa_parcel)
def rsa_parcel_from_piece(piece):
    return RsaParcel.from_piece(piece)
