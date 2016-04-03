from PySide import QtCore
from ..common.htypes import tServerPacket
from ..common.encrypted_packet import (
    tEncryptedPacket,
    make_session_key,
    encrypt_initial_packet,
    decrypt_subsequent_packet,
    )
from ..common.packet import AuxInfo, tPacket, Packet
from ..common.transport_packet import tTransportPacket, encode_transport_packet, decode_transport_packet
from ..common.packet_coders import packet_coders
from .transport import Transport, transport_registry
from .tcp_connection import TcpConnection


TRANSPORT_ID = 'encrypted_tcp'
ENCODING = 'cdr'


class Session(object):

    def __init__( self, session_key ):
        assert isinstance(session_key, str), repr(session_key)
        self.session_key = session_key


class EncryptedTransport(Transport):

    def send_packet( self, server, route, payload, payload_type, aux_info ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        server_public_key = server.get_endpoint().public_key
        connection = TcpConnection.produce(server_public_key, host, port)
        session = self._produce_session(connection.get_session_list())
        packet_data = self._make_packet(session, server_public_key, payload, payload_type, aux_info)
        connection.send_data(packet_data)
        return True

    def process_packet( self, session_list, server_public_key, data ):
        session = session_list.get_transport_session(TRANSPORT_ID)
        assert session is not None  # must be created when sending request
        encrypted_packet = packet_coders.decode(ENCODING, data, tEncryptedPacket)
        packet_data = decrypt_subsequent_packet(session.session_key, encrypted_packet)
        packet = packet_coders.decode(ENCODING, packet_data, tPacket)
        app = QtCore.QCoreApplication.instance()
        app.response_mgr.process_packet(server_public_key, packet, self._decode_payload)

    def _decode_payload( self, data ):
        return packet_coders.decode(ENCODING, data, tServerPacket)
    
    def _make_packet( self, session, server_public_key, payload, payload_type, aux_info ):
        if aux_info is None:
            aux_info = AuxInfo(requirements=[], modules=[])
        packet_data = packet_coders.encode(ENCODING, payload, payload_type)
        packet = Packet(aux_info, packet_data)
        packet_data = packet_coders.encode(ENCODING, packet, tPacket)
        encrypted_packet = encrypt_initial_packet(session.session_key, server_public_key, packet_data)
        encrypted_packet_data = packet_coders.encode(ENCODING, encrypted_packet, tEncryptedPacket)
        transport_packet = tTransportPacket.instantiate(TRANSPORT_ID, encrypted_packet_data)
        return encode_transport_packet(transport_packet)

    def _produce_session( self, session_list ):
        session = session_list.get_transport_session(TRANSPORT_ID)
        if session is None:
            session_key = make_session_key()
            session = Session(session_key)
            session_list.set_transport_session(TRANSPORT_ID, session)
        return session


transport_registry.register(TRANSPORT_ID, EncryptedTransport())
