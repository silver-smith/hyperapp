# server management module: used to expose module commands in one list

from object import ListDiff, ListObject, Command, Element, Column
from common.interface.server_management import server_management_iface
from module import Module


MODULE_NAME = 'management'


class CommandList(ListObject):

    iface = server_management_iface
    proxy_id = 'list'
    view_id = 'list'

    columns = [
        Column('key'),
        Column('module', 'Module'),
        Column('text', 'Name'),
        ]

    def __init__( self, path ):
        ListObject.__init__(self, path)

    def get_all_elements( self ):
        return map(self.cmd2element, Module.get_all_modules_commands())

    @staticmethod
    def cmd2element( cmd ):
        commands = [Command('open', 'Run', 'Run command')]
        id = '%s.%s' % (cmd.module_name, cmd.id)
        return Element(id, [id, cmd.module_name, cmd.text], commands)

    def process_request( self, request ):
        if request.command_id == 'open':
            return self.run_module_command(request)
        return ListObject.process_request(self, request)

    def run_module_command( self, request ):
        module_name, command_id = request.params.element_key.split('.')
        module = Module.get_module_by_name(module_name)
        return module.run_command(request, command_id)


class ManagementModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        return CommandList(path)


module = ManagementModule()
