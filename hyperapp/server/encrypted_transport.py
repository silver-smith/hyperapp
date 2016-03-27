from Queue import Queue
from ..common.htypes import tClientPacket, tServerPacket
from ..common.packet import tAuxInfo, tPacket, Packet
from ..common.encrypted_packet import ENCODING, tEncryptedInitialPacket, tEncryptedPacket, decrypt_initial_packet, encrypt_packet
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from .request import RequestBase
from .transport import Transport, transport_registry
from .transport_session import TransportSession


class EncryptedTcpSession(TransportSession):

    def __init__( self, transport ):
        assert isinstance(transport, EncryptedTcpTransport), repr(transport)
        TransportSession.__init__(self)
        self.transport = transport
        self.session_key = None
        self.updates = Queue()  # tUpdate list

    def send_update( self, update ):
        print '    update to be sent to %r channel %s' % (self.transport.get_transport_id(), self.get_id())

    def pop_updates( self ):
        return []

    def pull_notification_transport_packets( self ):
        return []


class EncryptedTcpTransport(Transport):

    def get_transport_id( self ):
        return 'encrypted_tcp'

    def register( self, registry ):
        registry.register(self.get_transport_id(), self)

    def process_packet( self, iface_registry, server, session_list, data ):
        session = session_list.get_transport_session(self.get_transport_id())
        if session is None:
           session = EncryptedTcpSession(self)
           session_list.set_transport_session(self.get_transport_id(), session)
        packet_data = self.decrypt_packet(server, session, data)
        packet = packet_coders.decode(ENCODING, packet_data, tPacket)
        request_rec = packet_coders.decode(ENCODING, packet.payload, tClientPacket)
        pprint(tClientPacket, request_rec)
        request = RequestBase.from_data(server, session, iface_registry, request_rec)

        result = server.process_request(request)

        if result is None:
            return
        aux_info, response_or_notification = result
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response_or_notification)
        packet_data = self.encode_response_or_notification(session, aux_info, response_or_notification)
        return packet_data

    def encode_response_or_notification( self, session, aux_info, response_or_notification ):
        assert session.session_key  # must be set when initial packet is received
        payload = packet_coders.encode(ENCODING, response_or_notification, tServerPacket)
        packet = Packet(aux_info, payload)
        packet_data = packet_coders.encode(ENCODING, packet, tPacket)
        encrypted_packet = encrypt_packet(session.session_key, packet_data)
        return packet_coders.encode(ENCODING, encrypted_packet, tEncryptedPacket)

    def decrypt_packet( self, server, session, data ):
        encrypted_initial_packet = packet_coders.decode(ENCODING, data, tEncryptedInitialPacket)
        session_key, plain_text = decrypt_initial_packet(server.get_identity(), encrypted_initial_packet)
        session.session_key = session_key
        return plain_text


EncryptedTcpTransport().register(transport_registry)
