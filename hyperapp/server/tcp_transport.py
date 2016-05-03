from Queue import Queue
from ..common.htypes import tUpdate, tClientPacket, tServerPacket
from ..common.packet import tAuxInfo, tPacket
from ..common.transport_packet import tTransportPacket
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from .request import PeerChannel, Peer, RequestBase, ServerNotification
from .transport import Transport, transport_registry
from .transport_session import TransportSession
from .server import Server


class TcpChannel(PeerChannel):

    def __init__( self, transport ):
        self.transport = transport
        self.updates = Queue()  # tUpdate list

    def _pop_all( self ):
        updates = []
        while not self.updates.empty():
            updates.append(self.updates.get())
        return list(reversed(updates))

    def send_update( self, update ):
        print '    update to be sent to %r channel %s' % (self.transport.get_transport_id(), self.get_id())
        self.updates.put(update)

    def pop_updates( self ):
        return self._pop_all()


class TcpSession(TransportSession):

    def __init__( self, transport ):
        assert isinstance(transport, TcpTransport), repr(transport)
        TransportSession.__init__(self)
        self.transport = transport
        self.channel = TcpChannel(transport)

    ## def __repr__( self ):
    ##     return 'TcpChannel'

    def pull_notification_transport_packets( self ):
        updates = self.channel._pop_all()
        if not updates:
            return []
        notification = ServerNotification()
        for update in updates:
            notification.add_update(update)
        notification_data = notification.to_data()
        aux_info = Server.prepare_aux_info(notification_data)
        print '-- sending notification to %r channel %s' % (self.transport.get_transport_id(), self.get_id())
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, notification_data)
        packet_data = self.transport.encode_response_or_notification(aux_info, notification_data)
        return [tTransportPacket(self.transport.get_transport_id(), packet_data)]


class TcpTransport(Transport):

    def __init__( self, encoding ):
        self.encoding = encoding

    def get_transport_id( self ):
        return 'tcp.%s' % self.encoding

    def register( self, registry ):
        registry.register(self.get_transport_id(), self)

    def process_packet( self, iface_registry, server, session_list, data ):
        session = session_list.get_transport_session(self.get_transport_id())
        if session is None:
           session = TcpSession(self)
           session_list.set_transport_session(self.get_transport_id(), session) 
        packet = packet_coders.decode(self.encoding, data, tPacket)
        request_rec = packet_coders.decode(self.encoding, packet.payload, tClientPacket)
        pprint(tClientPacket, request_rec)
        request = RequestBase.from_data(server, Peer(session.channel), iface_registry, request_rec)

        result = server.process_request(request)

        if result is None:
            return []
        aux_info, response_or_notification = result
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response_or_notification)
        packet_data = self.encode_response_or_notification(aux_info, response_or_notification)
        return [packet_data]

    def encode_response_or_notification( self, aux_info, response_or_notification ):
        payload = packet_coders.encode(self.encoding, response_or_notification, tServerPacket)
        packet = tPacket(aux_info, payload)
        packet_data = packet_coders.encode(self.encoding, packet, tPacket)
        return packet_data


TcpTransport('cdr').register(transport_registry)
TcpTransport('json').register(transport_registry)
