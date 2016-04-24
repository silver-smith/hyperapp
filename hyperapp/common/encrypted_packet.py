import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from .htypes import tBinary, Field, TRecord, TList, THierarchy
from .identity import Identity, PublicKey


ENCODING = 'cdr'
AES_KEY_SIZE = 256
AES_BLOCK_SIZE = 128
POP_CHALLENGE_SIZE = AES_BLOCK_SIZE*4


class HashMismatchError(Exception):
    pass


tEncryptedPacket = THierarchy('encrypted_packet')

tSubsequentEncryptedPacket = tEncryptedPacket.register('subsequent', fields=[
    Field('cbc_iv', tBinary),
    Field('encrypted_contents', tBinary),
    Field('hash', tBinary),
    ])

tInitialEncryptedPacket = tEncryptedPacket.register('initial', base=tSubsequentEncryptedPacket, fields=[
    Field('encrypted_session_key', tBinary),
    ])

tPopChallengePacket = tEncryptedPacket.register('pop_challenge', fields=[
    Field('challenge', tBinary),
    ])

tPopRecord = TRecord([
    Field('public_key_der', tBinary),  # SubjectPublicKeyInfo format
    Field('signature', tBinary),
    ])

tProofOfPossessionPacket = tEncryptedPacket.register('pop', fields=[
    Field('challenge', tBinary),
    Field('pop_records', TList(tPopRecord)),
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
    return tInitialEncryptedPacket.instantiate(cbc_iv, encrypted_contents, hash, encrypted_session_key)

def encrypt_subsequent_packet( session_key, plain_contents ):
    assert isinstance(session_key, str), repr(session_key)
    assert isinstance(plain_contents, str), repr(plain_contents)
    cbc_iv, encrypted_contents, hash = _encrypt(session_key, plain_contents)
    return tSubsequentEncryptedPacket.instantiate(cbc_iv, encrypted_contents, hash)

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

def decrypt_packet( identity, session_key, encrypted_packet ):
    assert isinstance(identity, Identity), repr(identity)
    tEncryptedPacket.validate('EncryptedPacket', encrypted_packet)
    if tEncryptedPacket.isinstance(encrypted_packet, tInitialEncryptedPacket):
        print len(encrypted_packet.encrypted_session_key), repr(encrypted_packet.encrypted_session_key)
        session_key = identity.decrypt(encrypted_packet.encrypted_session_key)
    else:
        assert session_key is not None  # session_key must be passed for subsequent packet
    plain_text = _decrypt(session_key, encrypted_packet)
    return (session_key, plain_text)

def decrypt_subsequent_packet( session_key, encrypted_packet ):
    tEncryptedPacket.validate('EncryptedPacket', encrypted_packet)
    assert not tEncryptedPacket.isinstance(encrypted_packet, tInitialEncryptedPacket)
    assert session_key is not None  # session_key must be passed for subsequent packet
    plain_text = _decrypt(session_key, encrypted_packet)
    return plain_text

def _decrypt( session_key, encrypted_packet ):
    assert isinstance(session_key, str), repr(session_key)
    # check hash first
    digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    digest.update(encrypted_packet.encrypted_contents)
    hash = digest.finalize()
    if hash != encrypted_packet.hash:
        raise HashMismatchError('encrypted_contents hash does not match')
    # decode session key and contents
    symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(encrypted_packet.cbc_iv), backend=default_backend())
    decryptor = symmetric_cipher.decryptor()
    padded_plaintext = decryptor.update(encrypted_packet.encrypted_contents) + decryptor.finalize()
    # unpad
    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    return plaintext
