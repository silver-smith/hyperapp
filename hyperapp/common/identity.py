from functools import total_ordering
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


RSA_KEY_SIZE = 4096  # use this key size when generating new identities


@total_ordering
class PublicKey(object):

    @classmethod
    def from_pem( cls, pem ):
        assert isinstance(pem, basestring), repr(pem)
        public_key = serialization.load_pem_public_key(str(pem), backend=default_backend())
        return cls('rsa', public_key)

    def __init__( self, algorithm, public_key ):
        assert isinstance(algorithm, basestring), repr(algorithm)
        self.algorithm = algorithm
        self.public_key = public_key
        self.public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        self._id = self._make_id()

    def _make_id( self ):
        pk_der = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(pk_der)
        return '%s' % digest.finalize()

    def get_id( self ):
        return self._id

    def get_short_id_hex( self ):
        return self._id[:4].encode('hex')

    def to_pem( self ):
        return self.public_pem

    def to_der( self ):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

    def save_to_file( self, fpath ):
        with open(fpath, 'w') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

    def encrypt( self, plain_text ):
        hash_alg = hashes.SHA1()
        cipher_text = self.public_key.encrypt(
            plain_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_alg),
                algorithm=hash_alg,
                label=None))
        return cipher_text

    def __eq__( self, other ):
        return isinstance(other, PublicKey) and self.public_pem == other.public_pem

    def __lt__( self, other ):
        return isinstance(other, PublicKey) and self.public_pem < other.public_pem


# Contains assymetryc private key
class Identity(object):

    @classmethod
    def load_from_file( cls, fpath ):
        with open(fpath) as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
        return cls('rsa', private_key)

    @classmethod
    def generate( cls ):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE,
            backend=default_backend()
        )
        return cls('rsa', private_key)

    def __init__( self, algorithm, private_key ):
        assert isinstance(algorithm, basestring), repr(algorithm)
        assert algorithm == 'rsa', repr(algorithm)  # only algorithm supported for now
        self.algorithm = algorithm
        self.private_key = private_key

    def save_to_file( self, fpath ):
        with open(fpath, 'w') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
                ))

    def get_public_key( self ):
        return PublicKey(self.algorithm, self.private_key.public_key())

    def decrypt( self, cipher_text ):
        hash_alg = hashes.SHA1()
        plain_text = self.private_key.decrypt(
            cipher_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hash_alg),
                algorithm=hash_alg,
                label=None))
        return plain_text

    def sign( self, message ):
        hashalg = hashes.SHA256()
        signer = self.private_key.signer(
            padding.PSS(
                mgf=padding.MGF1(hashalg),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256())
        signer.update(message)
        signature = signer.finalize()
        return 'rsa:sha256:%s' % signature
