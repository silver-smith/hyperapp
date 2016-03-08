from ..common.transport_packet import tTransportPacket


class TransportSession(object):

    def get_id( self ):
        return hex(id(self))[-6:]

    def pull_notification_transport_packets( self ):
        raise NotImplementedError(self.__class__)


class TransportSessionList(object):

    def __init__( self ):
        self.transport2session = {}  # transport id -> transport session

    def get_transport_session( self, transport_id ):
        session = self.transport2session.get(transport_id)
        if session is not None:
            print 'using %r session %s' % (transport_id, session.get_id())
        return session

    def set_transport_session( self, transport_id, session ):
        assert isinstance(session, TransportSession), repr(session)
        self.transport2session[transport_id] = session
        print 'created %r session %s' % (transport_id, session.get_id())

    def pull_notification_transport_packets( self ):
        packets = []
        for transport_id, session in self.transport2session.items():
            transport_packets = session.pull_notification_transport_packets()
            for packet in transport_packets:
                tTransportPacket.validate('<TransportPacket from %r>' % transport_id, packet)
            packets += transport_packets
        return packets
