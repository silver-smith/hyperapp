import uuid
from pony.orm import db_session, commit, desc, PrimaryKey, Required, Set
from .ponyorm_module import PonyOrmModule
from common.interface import Command, FormField, FormHandle
from common.interface.code_repository import module_list_iface, module_form_iface
from .object import Object, SmallListObject
from .module import ModuleCommand
from .form import stringFieldHandle


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
        return map(self.rec2element, module.Module.select().order_by(module.Module.id))

    @classmethod
    def rec2element( cls, rec ):
        commands = [Command('open', 'Open', 'Open module', 'Return')]
        return cls.Element(cls.Row(rec.name, rec.id), commands)

    def get_commands( self ):
        return [Command('add', 'Add', 'Create new module', 'Ins')]

    def process_request( self, request ):
        if request.command_id == 'add':
            return self.run_command_add(request)
        if request.command_id == 'open':
            return self.run_command_open(request)
        return SmallListObject.process_request(self, request)

    def run_command_add( self, request ):
        return request.make_response_handle(ModuleForm())

    @db_session
    def run_command_open( self, request ):
        id = request.params.element_key
        rec = module.Module[id]
        return request.make_response(ModuleForm(rec.id).get_handle(name=rec.name))


class ModuleForm(Object):

    iface = module_form_iface
    proxy_id = 'object'
    class_name = 'module_form'

    @classmethod
    def resolve( cls, path ):
        id = path.pop_str()
        path.check_empty()
        return cls(id)

    def __init__( self, id=None ):
        Object.__init__(self)
        self.id = id or None

    def get_path( self ):
        return module.make_path(self.class_name, self.id or '')

    def get_handle( self, name=None ):
        return FormHandle('form', self.get(), [
            FormField('name', stringFieldHandle(name)),
            ])

    def get_commands( self ):
        return [Command('submit', 'Submit', 'Submit form', 'Return')]

    def process_request( self, request ):
        if request.command_id == 'submit':
            return self.run_command_submit(request)
        return Object.process_request(self, request)

    @db_session
    def run_command_submit( self, request ):
        if self.id:
            rec = module.Module[self.id]
            rec.name = request.params.name
        else:
            id = str(uuid.uuid4())
            rec = module.Module(id=id,
                                name=request.params.name)
        commit()
        object = ModuleList()
        handle = ModuleList.ListHandle(object.get(), rec.id)
        return request.make_response(handle)

    

class CodeRepositoryModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2( self ):
        self.Module = self.make_entity('Module',
                                       id=PrimaryKey(unicode),
                                       name=Required(unicode),
                                       )

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == ModuleList.class_name:
            return ModuleList.resolve(path)
        if objname == ModuleForm.class_name:
            return ModuleForm.resolve(path)
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
