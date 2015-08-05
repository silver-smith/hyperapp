# server management module: used to expose module commands in one list

from common.interface import Command, Column
from common.interface.server_management import server_management_iface
from object import SmallListObject
from module import Module


MODULE_NAME = 'management'


class CommandList(SmallListObject):

    iface = server_management_iface
    proxy_id = 'list'

    columns = [
        Column('key'),
        Column('module', 'Module'),
        Column('text', 'Name'),
        ]

    def __init__( self ):
        SmallListObject.__init__(self)

    def get_path( self ):
        return module.make_path()

    def fetch_all_elements( self ):
        return map(self.cmd2element, Module.get_all_modules_commands())

    @classmethod
    def cmd2element( cls, cmd ):
        commands = [Command('open', 'Run', 'Run command')]
        id = '%s.%s' % (cmd.module_name, cmd.id)
        return cls.Element(cls.Row(id, cmd.module_name, cmd.text), commands)

    def process_request( self, request ):
        if request.command_id == 'open':
            return self.run_module_command(request)
        return SmallListObject.process_request(self, request)

    def run_module_command( self, request ):
        module_name, command_id = request.params.element_key.split('.')
        module = Module.get_module_by_name(module_name)
        return module.run_command(request, command_id)


class ManagementModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        path.check_empty()
        return CommandList()


module = ManagementModule()
