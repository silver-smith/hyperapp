from PySide import QtCore
from ..common.htypes import tServerPacket
from ..common.encrypted_packet import (
    tEncryptedPacket,
    tSubsequentEncryptedPacket,
    tPopChallengePacket,
    tPopRecord,
    tProofOfPossessionPacket,
    make_session_key,
    encrypt_initial_packet,
    decrypt_subsequent_packet,
    )
from ..common.packet import tAuxInfo, tPacket
from ..common.transport_packet import tTransportPacket, encode_transport_packet, decode_transport_packet
from ..common.packet_coders import packet_coders
from .transport import Transport, transport_registry
from .tcp_connection import TcpConnection
from .identity import get_identity_controller


TRANSPORT_ID = 'encrypted_tcp'
ENCODING = 'cdr'


class Session(object):

    def __init__( self, session_key ):
        assert isinstance(session_key, bytes), repr(session_key)
        self.session_key = session_key


class EncryptedTransport(Transport):

    def send_packet( self, server, route, payload, payload_type, aux_info ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        server_public_key = server.get_endpoint().public_key
        connection = TcpConnection.produce(server_public_key, host, port)
        session = self._produce_session(connection.get_session_list())
        packet_data = self._make_payload_packet(session, server_public_key, payload, payload_type, aux_info)
        connection.send_data(packet_data)
        return True

    def process_packet( self, connection, session_list, server_public_key, data ):
        session = session_list.get_transport_session(TRANSPORT_ID)
        assert session is not None  # must be created when sending request
        encrypted_packet = packet_coders.decode(ENCODING, data, tEncryptedPacket)
        if isinstance(encrypted_packet, tSubsequentEncryptedPacket):
            self.process_subsequent_encrypted_packet(server_public_key, session, encrypted_packet)
        if isinstance(encrypted_packet, tPopChallengePacket):
            self.process_pop_challenge_packet(connection, server_public_key, session, encrypted_packet)

    def process_subsequent_encrypted_packet( self, server_public_key, session, encrypted_packet ):
        packet_data = decrypt_subsequent_packet(session.session_key, encrypted_packet)
        packet = packet_coders.decode(ENCODING, packet_data, tPacket)
        app = QtCore.QCoreApplication.instance()
        app.response_mgr.process_packet(server_public_key, packet, self._decode_payload)

    def process_pop_challenge_packet( self, connection, server_public_key, session, encrypted_packet ):
        challenge = encrypted_packet.challenge
        pop_records = []
        for item in get_identity_controller().get_items():
            pop_records.append(tPopRecord(
                item.identity.get_public_key().to_der(),
                item.identity.sign(challenge)))
        pop_packet = tProofOfPossessionPacket(challenge, pop_records)
        transport_packet_data = self._make_transport_packet(pop_packet)
        connection.send_data(transport_packet_data)
        
    def _decode_payload( self, data ):
        return packet_coders.decode(ENCODING, data, tServerPacket)
    
    def _make_payload_packet( self, session, server_public_key, payload, payload_type, aux_info ):
        if aux_info is None:
            aux_info = tAuxInfo(requirements=[], modules=[])
        packet_data = packet_coders.encode(ENCODING, payload, payload_type)
        packet = tPacket(aux_info, packet_data)
        packet_data = packet_coders.encode(ENCODING, packet, tPacket)
        encrypted_packet = encrypt_initial_packet(session.session_key, server_public_key, packet_data)
        return self._make_transport_packet(encrypted_packet)

    def _make_transport_packet( self, encrypted_packet ):
        encrypted_packet_data = packet_coders.encode(ENCODING, encrypted_packet, tEncryptedPacket)
        transport_packet = tTransportPacket(TRANSPORT_ID, encrypted_packet_data)
        return encode_transport_packet(transport_packet)

    def _produce_session( self, session_list ):
        session = session_list.get_transport_session(TRANSPORT_ID)
        if session is None:
            session_key = make_session_key()
            session = Session(session_key)
            session_list.set_transport_session(TRANSPORT_ID, session)
        return session


transport_registry.register(TRANSPORT_ID, EncryptedTransport())
