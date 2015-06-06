
class ServerNotification(object):

    def __init__( self, peer ):
        self.peer = peer
        self.updates = []  # (path, ListDiff) list

    def add_update( self, path, diff ):
        self.updates.append((path, diff))

    def as_json( self ):
        d = dict()
        if self.updates:
            d['updates'] = [(path, diff.as_json()) for path, diff in self.updates]
        return d


class Response(ServerNotification):

    def __init__( self, peer, iface, command_id, request_id, result_dict=None ):
        ServerNotification.__init__(self, peer)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.object = None
        self.result_dict = result_dict

    def as_json( self ):
        d = ServerNotification.as_json(self)
        d['request_id'] = self.request_id
        if self.object:
            d['object'] = self.object
        if self.result_dict:
            d['result'] = self.result_dict
        return d

    def pprint( self ):
        pprint.pprint(self.as_json())

    def encode( self, encoder ):
        return encoder.encode(self.get_packet_type(), self.as_json())

    def get_packet_type( self ):
        return self.iface.get_response_type(self.command_id)


class ClientNotification(object):

    def __init__( self, peer, iface, path, command_id, params ):
        self.peer = peer
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params

    def encode( self, encoder ):
        return encoder.encode(self.get_packet_type(), self.as_dict())

    def as_dict( self ):
        return dict(
            iface_id=self.iface.iface_id,
            path=self.path,
            command=self.command_id,
            params=self.params)

    def get_packet_type( self ):
        return self.iface.get_client_notification_type(self.command_id)


class Request(ClientNotification):

    def __init__( self, peer, iface, path, command_id, request_id, params ):
        ClientNotification.__init__(self, peer, iface, path, command_id, params)
        self.request_id = request_id

    def as_dict( self ):
        return dict(ClientNotification.as_dict(self),
                    request_id=self.request_id)

    def get_packet_type( self ):
        return self.iface.get_request_type(self.command_id)

    def make_response( self, result_dict=None ):
        return Response(self.peer, self.iface, self.command_id, self.request_id, result_dict)

    def make_response_object( self, obj ):
        self.iface.validate_result(self.command_id, obj)
        return self.make_response(obj)

    def make_response_result( self, **kw ):
        self.iface.validate_result(self.command_id, kw)
        return self.make_response(kw)

    def make_response_update( self, path, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        response = self.make_response()
        response.add_update(path, diff)
        return response
