import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from .transport import Transport, transports
from .tcp_connection import TcpConnection


class HashMismatchError(Exception): pass


class Header(object):

    struct_format = '!IIII'

    @classmethod
    def size( cls ):
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode( cls, data ):
        encrypted_session_key_size, cbc_iv_size, encrypted_contents_size, hash_size = struct.unpack(cls.struct_format, data)
        return cls(encrypted_session_key_size, cbc_iv_size, encrypted_contents_size, hash_size)

    def __init__( self, encrypted_session_key_size, cbc_iv_size, encrypted_contents_size, hash_size ):
        self.encrypted_session_key_size = encrypted_session_key_size
        self.cbc_iv_size = cbc_iv_size
        self.encrypted_contents_size = encrypted_contents_size
        self.hash_size = hash_size

    def encode( self ):
        return struct.pack(self.struct_format,
                           self.encrypted_session_key_size, self.cbc_iv_size, self.encrypted_contents_size, self.hash_size)

class EncryptedPacket(object):

    @classmethod
    def has_full_packet( cls, data ):
        hsize = Header.size()
        if len(data) < hsize:
            return False
        header = Header.decode(data[:hsize])
        return len(data) >= hsize \
           + header.encrypted_session_key_size \
           + header.cbc_iv_size \
           + header.encrypted_contents_size \
           + header.hash_size

    @classmethod
    def decode( cls, data ):
        assert cls.has_full_packet(data)
        hsize = Header.size()
        header = Header.decode(data[:hsize])
        ofs = hsize
        encrypted_session_key = data[ofs:ofs + header.encrypted_session_key_size]
        ofs += header.encrypted_session_key_size
        cbc_iv = data[ofs:ofs + header.cbc_iv_size]
        ofs += header.cbc_iv_size
        encrypted_contents = data[ofs:ofs + header.encrypted_contents_size]
        ofs += header.encrypted_contents_size
        hash = data[ofs:ofs + header.hash_size]
        packet_size = ofs + header.hash_size
        return packet_size

    @classmethod
    def encrypt( cls, public_key, plain_contents ):
        # generate session key and CBC initialization vector
        session_key = os.urandom(32)
        cbc_iv = os.urandom(16)
        # encrypt session key
        encrypted_session_key = public_key.encrypt(session_key)
        # encrypt contents
        symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(cbc_iv), backend=default_backend())
        encryptor = symmetric_cipher.encryptor()
        encrypted_contents = encryptor.update(plain_contents) + encryptor.finalize()
        # make hash
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(encrypted_contents)
        hash = digest.finalize()
        # done
        return cls(encrypted_session_key, cbc_iv, encrypted_contents, hash)

    def __init__( self, encrypted_session_key, cbc_iv, encrypted_contents, hash ):
        self.encrypted_session_key = encrypted_session_key
        self.cbc_iv = cbc_iv
        self.encrypted_contents = encrypted_contents
        self.hash = hash

    header_format = '!III'

    def encode( self ):
        header = Header(len(self.encrypted_session_key), len(self.cbc_iv), len(self.encrypted_contents), len(self.hash))
        return header.encode() + self.encrypted_session_key + self.cbc_iv + self.encrypted_contents + self.hash

    def decrypt( self, identity ):
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(self.encrypted_contents)
        hash = digest.finalize()
        if hash != self.hash:
            raise HashMismatchError('Hash for received message does not match')
        session_key = identity.decrypt(self.encrypted_session_key)
        symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(self.cbc_iv), backend=default_backend())
        decryptor = symmetric_cipher.decryptor()
        plain_context = decryptor.update(self.encrypted_contents) + decryptor.finalize()
        return plain_context


class EncryptedTransport(Transport):

    connections = {}  # (server public key, host, port) -> Connection

    def send_packet( self, server, route, packet ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        connection = self._produce_connection(server, host, port)
        encrypted_packet = EncryptedPacket.encrypt(server.get_endpoint.public_key, packet.encode())
        connection.send_data(encrypted_packet.encode())

    def _produce_connection( self, server, host, port ):
        key = (server.endpoint.public_key, host, port)
        connection = self.connections.get(key)
        if not connection:
            connection = TcpConnection(host, port, DataConsumer(server))
            self.connections[key] = connection
        return connection


transports.register('encrypted_tcp', EncryptedTransport())
