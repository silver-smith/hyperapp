# server management module: used to expose module commands in one list

from ..common.htypes import tCommand
from ..common.interface.server_management import server_management_iface
from ..common.url import Url
from .object import SmallListObject
from .module import Module


MODULE_NAME = 'management'


class CommandList(SmallListObject):

    iface = server_management_iface
    objimpl_id = 'proxy_list'

    @classmethod
    def get_path( cls ):
        return module.make_path()

    def __init__( self ):
        SmallListObject.__init__(self)

    def fetch_all_elements( self ):
        return list(map(self.cmd2element, Module.get_all_modules_commands()))

    @classmethod
    def cmd2element( cls, cmd ):
        commands = [tCommand('open', kind='element', resource_id='', is_default_command=True)]
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

    def resolve( self, iface, path ):
        path.check_empty()
        return CommandList()


def get_management_url( public_key ):
    return Url(CommandList.iface, public_key, CommandList.get_path())


module = ManagementModule()
