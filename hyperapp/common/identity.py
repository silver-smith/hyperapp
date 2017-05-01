from functools import total_ordering
import codecs
import cryptography.exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


RSA_KEY_SIZE_SAFE = 4096  # key size used when generating new identities
RSA_KEY_SIZE_FAST = 1024  # used for testing


@total_ordering
class PublicKey(object):

    @classmethod
    def from_pem(cls, pem):
        assert isinstance(pem, str), repr(pem)
        public_key = serialization.load_pem_public_key(pem.encode(), backend=default_backend())
        return cls('rsa', public_key)

    @classmethod
    def from_der(cls, der):
        assert isinstance(der, bytes), repr(der)
        public_key = serialization.load_der_public_key(der, backend=default_backend())
        return cls('rsa', public_key)

    def __init__(self, algorithm, public_key):
        assert isinstance(algorithm, str), repr(algorithm)
        self.algorithm = algorithm
        self.public_key = public_key
        self.public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        self._id = self._make_id()

    def _make_id(self):
        pk_der = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(pk_der)
        return digest.finalize()

    def get_id(self):
        return self._id

    def get_id_hex(self):
        return codecs.encode(self._id, 'hex').decode()

    def get_short_id_hex(self):
        return codecs.encode(self._id[:4], 'hex').decode()

    def to_pem(self):
        return self.public_pem

    def to_der(self):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

    def save_to_file(self, fpath):
        with open(fpath, 'w') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

    def encrypt(self, plain_text):
        hash_alg = hashes.SHA1()
        cipher_text = self.public_key.encrypt(
            plain_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_alg),
                algorithm=hash_alg,
                label=None))
        return cipher_text

    def verify(self, message, signature):
        sign_alg, hash_alg, sign = signature.split(b':', 2)
        assert sign_alg == b'rsa' and hash_alg == b'sha256', repr((sign_alg, hash_alg))
        hashalg = hashes.SHA256()
        verifier = self.public_key.verifier(
            sign,
            padding.PSS(
                mgf=padding.MGF1(hashalg),
                salt_length=padding.PSS.MAX_LENGTH),
            hashalg)
        verifier.update(message)
        try:
            verifier.verify()
            return True
        except cryptography.exceptions.InvalidSignature:
            return False

    def __eq__(self, other):
        return isinstance(other, PublicKey) and self.public_pem == other.public_pem

    def __lt__(self, other):
        return isinstance(other, PublicKey) and self.public_pem < other.public_pem

    def __hash__(self):
        return hash(self.public_pem)


# Contains assymetryc private key
class Identity(object):

    @classmethod
    def load_from_file(cls, fpath):
        with open(fpath, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
        return cls('rsa', private_key)

    @classmethod
    def generate(cls, fast=False):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE_FAST if fast else RSA_KEY_SIZE_SAFE,
            backend=default_backend()
        )
        return cls('rsa', private_key)

    def __init__(self, algorithm, private_key):
        assert isinstance(algorithm, str), repr(algorithm)
        assert algorithm == 'rsa', repr(algorithm)  # only algorithm supported for now
        self.algorithm = algorithm
        self.private_key = private_key

    def save_to_file(self, fpath):
        with open(fpath, 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
                ))

    def get_public_key(self):
        return PublicKey(self.algorithm, self.private_key.public_key())

    def decrypt(self, cipher_text):
        hash_alg = hashes.SHA1()
        plain_text = self.private_key.decrypt(
            cipher_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_alg),
                algorithm=hash_alg,
                label=None))
        return plain_text

    def sign(self, message):
        hashalg = hashes.SHA256()
        signer = self.private_key.signer(
            padding.PSS(
                mgf=padding.MGF1(hashalg),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashalg)
        signer.update(message)
        signature = signer.finalize()
        return b'rsa:sha256:' + signature
