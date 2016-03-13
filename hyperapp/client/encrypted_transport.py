import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from ..common.htypes import tString, tBinary, Field, TRecord
from ..common.encrypted_packet import tEncryptedPacket
from ..common.transport_packet import tTransportPacket
from .transport import Transport, transport_registry
from .tcp_connection import TcpConnection


class HashMismatchError(Exception): pass


TRANSPORT_ID = 'encrypted_tcp'
ENCODING = 'cdr'
    


    ## def decrypt( self, identity ):
    ##     digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    ##     digest.update(self.encrypted_contents)
    ##     hash = digest.finalize()
    ##     if hash != self.hash:
    ##         raise HashMismatchError('Hash for received message does not match')
    ##     session_key = identity.decrypt(self.encrypted_session_key)
    ##     symmetric_cipher = Cipher(algorithms.AES(session_key), modes.CBC(self.cbc_iv), backend=default_backend())
    ##     decryptor = symmetric_cipher.decryptor()
    ##     plain_context = decryptor.update(self.encrypted_contents) + decryptor.finalize()
    ##     return plain_context


class Session(object):

    def __init__( self, session_key, cbc_iv ):
        assert isinstance(session_key, str), repr(session_key)
        assert isinstance(cbc_iv, str), repr(cbc_iv)
        self.session_key = session_key
        self.cbc_iv = cbc_iv  # CBC initialization vector


class EncryptedTransport(Transport):

    def send_packet( self, server, route, packet ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)

        rec = encrypt(server.get_endpoint.public_key, packet.encode())
        transport_packet = tTransportPacket.instantiate(transport_id=TRANPORT_ID, data=rec.encode())
        connection.send_data(transport_packet.encode())

        server_public_key = server.get_endpoint().public_key
        connection = TcpConnection.produce(server_public_key, host, port)
        session = self._produce_session(connection.produce_session_list())
        packet_data = self._make_packet(session, server_public_key, payload, payload_type, aux_info)
        connection.send_data(packet_data)
        return True

    def _make_packet( self, session, server_public_key, payload, payload_type, aux_info ):
        if aux_info is None:
            aux_info = AuxInfo(requirements=[], modules=[])
        packet_data = packet_coders.encode(ENCODING, payload, payload_type)
        packet = Packet(aux_info, packet_data)
        packet_data = packet_coders.encode(ENCODING, packet, tPacket)
        encrypted_packet = self._encrypt_packet(session, server_public_key, packet_data)
        encrypted_packet_data = packet_coders.encode(ENCODING, encrypted_packet, tEncryptedInitialPacket)
        transport_packet = tTransportPacket.instantiate(TRANSPORT_ID, encrypted_packet_data)
        return encode_transport_packet(transport_packet)

    def _produce_session( self, session_list ):
        session = session_list.get_transport_session(TRANSPORT_ID)
        if session is None:
            session_key = os.urandom(32)
            cbc_iv = os.urandom(16)
            session = Session(session_key, cbc_iv)
            session_list.set_transport_session(TRANSPORT_ID)
        return session.session_key

    def _encrypt_packet( self, session, server_public_key, plain_contents ):
        # encrypt session key
        encrypted_session_key = public_key.encrypt(session.session_key)
        # encrypt contents
        symmetric_cipher = Cipher(algorithms.AES(session.session_key), modes.CBC(session.cbc_iv), backend=default_backend())
        encryptor = symmetric_cipher.encryptor()
        encrypted_contents = encryptor.update(plain_contents) + encryptor.finalize()
        # make hash
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(encrypted_contents)
        hash = digest.finalize()
        # done
        return tEncryptedInitialPacket.instantiate(encrypted_session_key, cbc_iv, encrypted_contents, hash)


transport_registry.register(TRANSPORT_ID, EncryptedTransport())
