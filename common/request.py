

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
        params_type = self.iface.get_command_params_type(self.command_id)
        return TRecord([
            Field('iface_id', TString()),
            Field('path', TPath()),
            Field('command', TString()),
            Field('params', params_type),
            ])


class Request(ClientNotification):

    def __init__( self, peer, iface, path, command_id, request_id, params ):
        ClientNotification.__init__(self, peer, iface, path, command_id, params)
        self.request_id = request_id

    def as_dict( self ):
        return dict(ClientNotification.as_dict(self),
                    request_id=self.request_id)

    def get_packet_type( self ):
        params_type = self.iface.get_command_params_type(self.command_id)
        return TRecord([
            Field('iface_id', TString()),
            Field('path', TPath()),
            Field('command', TString()),
            Field('request_id', TString()),
            Field('params', params_type),
            ])
