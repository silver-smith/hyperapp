from .htypes import tBinary, Field, TRecord


tEncryptedInitialPacket = TRecord([
    Field('encrypted_session_key', tBinary),
    Field('cbc_iv', tBinary),
    Field('encrypted_contents', tBinary),
    Field('hash', tBinary),
    ])

tEncryptedPacket = TRecord([
    Field('encrypted_contents', tBinary),
    Field('hash', tBinary),
    ])
