from pony.orm import db_session, commit, desc, PrimaryKey, Required, Set
from .ponyorm_module import PonyOrmModule
from common.interface.code_repository import module_list_iface
from .module import ModuleCommand
from .object import SmallListObject


MODULE_NAME = 'code_repository'


class ModuleList(SmallListObject):

    iface = module_list_iface
    proxy_id = 'list'
    class_name = 'module_list'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        path.check_empty()
        return cls()

    @classmethod
    def get_path( cls ):
        return module.make_path(cls.class_name)

    @db_session
    def fetch_all_elements( self ):
        return map(self.rec2element, module.ModuleEntry.select().order_by(module.ModuleEntry.id))

    @classmethod
    def rec2element( cls, rec ):
        commands = []
        return cls.Element(cls.Row(rec.name, rec.id), commands)


class CodeRepositoryModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2( self ):
        self.ModuleEntry = self.make_entity('Module',
                                            id=PrimaryKey(unicode),
                                            name=Required(unicode),
                                            )

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == ModuleList.class_name:
            return ModuleList.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [
            ModuleCommand('open_module_list', 'Modules', 'Open module list', 'Alt+M', self.name),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'open_module_list':
            return request.make_response_handle(ModuleList())
        return PonyOrmModule.run_command(self, request, command_id)


module = CodeRepositoryModule()
