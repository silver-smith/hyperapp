

class TransportSessionList(object):

    def __init__( self ):
        self.transport2session = {}  # transport id -> transport session

    def get_transport_session( self, transport_id ):
        return self.transport2session.get(transport_id)

    def set_transport_session( self, transport_id, session ):
        #assert isinstance(session, TransportSession), repr(session)
        self.transport2session[transport_id] = session
