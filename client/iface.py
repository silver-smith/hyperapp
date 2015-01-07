from command import ObjectCommand
import iface_registry


class ObjectIface(object):

    def __init__( self, server, response ):
        self.server = server
        self.path = response['path']
        self.commands = [ObjectCommand.from_json(cmd) for cmd in response['commands']]

    def get_title( self ):
        return self.path

    def get_commands( self ):
        return self.commands


iface_registry.register_iface('object', ObjectIface)
