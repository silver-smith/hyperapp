from command import ObjectCommand
import iface_registry


class ProxyObject(object):

    def __init__( self, server, path, commands ):
        self.server = server
        self.path = path
        self.commands = commands

    @staticmethod
    def parse_resp( resp ):
        path = resp['path']
        commands = [ObjectCommand.from_json(cmd) for cmd in resp['commands']]
        return (path, commands)

    def get_title( self ):
        return ','.join('%s=%s' % (key, value) for key, value in self.path.items())

    def get_commands( self ):
        return self.commands

    def make_command_request( self, command_id ):
        return dict(
            method='run_command',
            path=self.path,
            command_id=command_id,
            )

    def run_command( self, command_id ):
        request = self.make_command_request(command_id)
        return self.server.request_an_object(request)


## iface_registry.register_iface('object', ProxyObject)
