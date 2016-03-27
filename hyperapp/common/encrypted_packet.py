import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from .htypes import tBinary, Field, TRecord
from .identity import Identity, PublicKey


ENCODING = 'cdr'
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

def encrypt_initial_packet( session_key, server_public_key, plain_contents ):
    assert isinstance(session_key, str), repr(session_key)
    assert isinstance(server_public_key, PublicKey), repr(server_public_key)
    assert isinstance(plain_contents, str), repr(plain_contents)
    # encrypt session key
    encrypted_session_key = server_public_key.encrypt(session_key)
    cbc_iv, encrypted_contents, hash = _encrypt(session_key, plain_contents)
    return tEncryptedInitialPacket.instantiate(encrypted_session_key, cbc_iv, encrypted_contents, hash)

def encrypt_packet( session_key, plain_contents ):
    assert isinstance(session_key, str), repr(session_key)
    assert isinstance(plain_contents, str), repr(plain_contents)
    cbc_iv, encrypted_contents, hash = _encrypt(session_key, plain_contents)
    return tEncryptedPacket.instantiate(cbc_iv, encrypted_contents, hash)

def _encrypt( session_key, plain_contents ):
    assert isinstance(session_key, str), repr(session_key)
    assert isinstance(plain_contents, str), repr(plain_contents)
    # pad plaintext to block size
    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_plain_contents = padder.update(plain_contents) + padder.finalize()
    # create CBC initialization vector
    cbc_iv = os.urandom(AES_BLOCK_SIZE/8)
    # encrypt contents
    symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(cbc_iv), backend=default_backend())
    encryptor = symmetric_cipher.encryptor()
    encrypted_contents = encryptor.update(padded_plain_contents) + encryptor.finalize()
    # make hash
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(encrypted_contents)
    hash = digest.finalize()
    # done
    return (cbc_iv, encrypted_contents, hash)

def decrypt_initial_packet( identity, encrypted_initial_packet ):
    assert isinstance(identity, Identity), repr(identity)
    tEncryptedInitialPacket.validate('EncryptedInitialPacket', encrypted_initial_packet)
    session_key = identity.decrypt(encrypted_initial_packet.encrypted_session_key)
    plain_text = _decrypt(session_key, encrypted_initial_packet)
    return (session_key, plain_text)

def decrypt_packet( session_key, encrypted_packet ):
    assert isinstance(session_key, str), repr(session_key)
    tEncryptedPacket.validate('EncryptedPacket', encrypted_packet)
    return _decrypt(session_key, encrypted_packet)

def _decrypt( session_key, encrypted_packet ):
    assert isinstance(session_key, str), repr(session_key)
    # check hash first
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(encrypted_packet.encrypted_contents)
    hash = digest.finalize()
    if hash != encrypted_packet.hash:
        raise RuntimeError('encrypted_contents hash does not match')
    # decode session key and contents
    symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(encrypted_packet.cbc_iv), backend=default_backend())
    decryptor = symmetric_cipher.decryptor()
    padded_plaintext = decryptor.update(encrypted_packet.encrypted_contents) + decryptor.finalize()
    # unpad
    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    return plaintext
