import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from .htypes import tBinary, Field, TRecord
from .identity import PublicKey


AES_KEY_SIZE = 256
AES_BLOCK_SIZE = 128


tEncryptedInitialPacket = TRecord([
    Field('encrypted_session_key', tBinary),
    Field('cbc_iv', tBinary),
    Field('encrypted_contents', tBinary),
    Field('hash', tBinary),
    ])

tEncryptedPacket = TRecord([
    Field('cbc_iv', tBinary),
    Field('encrypted_contents', tBinary),
    Field('hash', tBinary),
    ])


def make_session_key():
    return os.urandom(AES_KEY_SIZE/8)

def encrypt_packet( session_key, server_public_key, plain_contents ):
    assert isinstance(session_key, str), repr(session_key)
    assert isinstance(server_public_key, PublicKey), repr(server_public_key)
    assert isinstance(plain_contents, str), repr(plain_contents)
    # pad plaintext to block size
    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_plain_contents = padder.update(plain_contents) + padder.finalize()
    # create CBC initialization vector
    cbc_iv = os.urandom(AES_BLOCK_SIZE/8)
    # encrypt session key
    encrypted_session_key = server_public_key.encrypt(session_key)
    # encrypt contents
    symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(cbc_iv), backend=default_backend())
    encryptor = symmetric_cipher.encryptor()
    encrypted_contents = encryptor.update(padded_plain_contents) + encryptor.finalize()
    # make hash
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(encrypted_contents)
    hash = digest.finalize()
    # done
    return tEncryptedInitialPacket.instantiate(encrypted_session_key, cbc_iv, encrypted_contents, hash)
