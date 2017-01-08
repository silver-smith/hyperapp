import uuid
from pony.orm import db_session, select, commit, desc, PrimaryKey, Required, Set
from ..common.interface import core as core_types
from ..common.interface import form as form_types
from ..common.interface import splitter as splitter_types
from ..common.interface import module_list as module_list_types
from .ponyorm_module import PonyOrmModule
from .command import command
from .object import Object, SmallListObject, subscription
from .module import ModuleCommand
from .form import stringFieldHandle, formHandle


MODULE_NAME = 'module_list'


def splitter_handle( x, y ):
    return splitter_types.splitter_handle('splitter', x, y, orientation='horizontal', focused=0, sizes=[])


class ModuleList(SmallListObject):

    iface = module_list_types.module_list
    objimpl_id = 'proxy_list'
    class_name = 'module_list'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        path.check_empty()
        return cls()

    @classmethod
    def get_path( cls ):
        return this_module.make_path(cls.class_name)

    def __init__( self ):
        SmallListObject.__init__(self, core_types)

    @db_session
    def fetch_all_elements( self ):
        return list(map(self.rec2element, this_module.Module.select().order_by(this_module.Module.id)))

    @classmethod
    def rec2element( cls, rec ):
        commands = [cls.command_open, cls.command_deps, cls.command_delete]
        return cls.Element(cls.Row(rec.name, rec.id), commands)

    @command('add')
    def command_add( self, request ):
        return request.make_response_object(ModuleForm())

    @command('delete', kind='element')
    @db_session
    def command_delete( self, request ):
        id = request.params.element_key
        this_module.Module[id].delete()
        diff = self.Diff_delete(id)
        return request.make_response_update(self.iface, self.get_path(), diff)

    @command('deps', kind='element')
    @db_session
    def command_deps( self, request ):
        module_id = request.params.element_key
        dep_list = ModuleDepList(module_id)
        available_list = AvailableDepList(module_id)
        dep_list.subscribe(request)
        available_list.subscribe(request)
        return request.make_response_handle(
            splitter_handle(dep_list.get_handle(request), available_list.get_handle(request)))

    @command('open', kind='element', is_default_command=True)
    @db_session
    def command_open( self, request ):
        id = request.params.element_key
        rec = this_module.Module[id]
        return request.make_response_handle(ModuleForm(rec.id).get_handle(request, name=rec.name))


class ModuleForm(Object):

    iface = module_list_types.module_form
    objimpl_id = 'proxy'
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
        return this_module.make_path(self.class_name, self.id or '')

    def get_handle( self, request, name=None ):
        return formHandle(self.get(request), [
            form_types.form_field('name', stringFieldHandle(name)),
            ])

    @command('submit', is_default_command=True)
    @db_session
    def command_submit( self, request ):
        if self.id:
            rec = this_module.Module[self.id]
            rec.name = request.params.name
        else:
            id = str(uuid.uuid4())
            rec = this_module.Module(id=id,
                                name=request.params.name)
        object = ModuleList()
        handle = ModuleList.ListHandle(object.get(request), key=rec.id)
        return request.make_response_handle(handle)


class ModuleDepList(SmallListObject):

    iface = module_list_types.module_dep_list
    objimpl_id = 'proxy_list'
    class_name = 'module_dep_list'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        module_id = path.pop_str()
        assert module_id, repr(module_id)
        path.check_empty()
        return cls(module_id)

    def __init__( self, module_id=None ):
        SmallListObject.__init__(self, core_types)
        self.module_id = module_id or None

    def get_path( self ):
        return this_module.make_path(self.class_name, self.module_id)

    @db_session
    def fetch_all_elements( self ):
        rec = this_module.Module[self.module_id]
        return list(map(self.rec2element, rec.deps))

    @classmethod
    def rec2element( cls, rec ):
        commands = [cls.command_remove]
        return cls.Element(cls.Row(rec.id, rec.visible_as, rec.dep.id), commands)

    @command('remove', kind='element')
    @db_session
    def command_remove( self, request ):
        rec_id = request.params.element_key
        rec = this_module.ModuleDep[rec_id]
        dep_module_rec = rec.dep
        rec.delete()
        available_list = AvailableDepList(self.module_id)
        add_diff = available_list.Diff_insert_one(dep_module_rec.id, available_list.rec2element(dep_module_rec))
        subscription.distribute_update(available_list.iface, available_list.get_path(), add_diff)
        remove_diff = self.Diff_delete(rec_id)
        return request.make_response_update(self.iface, self.get_path(), remove_diff)


class AvailableDepList(SmallListObject):

    iface = module_list_types.available_dep_list
    objimpl_id = 'proxy_list'
    class_name = 'available_dep_list'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        module_id = path.pop_str()
        assert module_id, repr(module_id)
        path.check_empty()
        return cls(module_id)

    def __init__( self, module_id=None ):
        SmallListObject.__init__(self, core_types)
        self.module_id = module_id or None

    def get_path( self ):
        return this_module.make_path(self.class_name, self.module_id)

    @db_session
    def fetch_all_elements( self ):
        dep_ids = set([dep.dep.id for dep in this_module.Module[self.module_id].deps])
        if dep_ids:
            query = select(rec for rec in this_module.Module if rec.id not in dep_ids)
        else:
            query = select(rec for rec in this_module.Module)
        return list(map(self.rec2element, query.order_by(this_module.Module.id)))

    @classmethod
    def rec2element( cls, rec ):
        commands = [cls.command_add]
        return cls.Element(cls.Row(rec.name, rec.id), commands)

    @command('add', kind='element')
    @db_session
    def command_add( self, request ):
        module_id = request.params.element_key
        dep_module = this_module.Module[module_id]
        module_rec = this_module.Module[self.module_id]
        rec = this_module.ModuleDep(module=module_rec, dep=dep_module, visible_as=dep_module.name)
        commit()  # generate rec.id
        dep_list = ModuleDepList(self.module_id)
        add_diff = dep_list.Diff_insert_one(rec.id, dep_list.rec2element(rec))
        subscription.distribute_update(dep_list.iface, dep_list.get_path(), add_diff)
        remove_diff = self.Diff_delete(module_id)
        return request.make_response_update(self.iface, self.get_path(), remove_diff)
    

class ThisModule(PonyOrmModule):

    def __init__( self, services ):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2( self ):
        self.Module = self.make_entity('Module',
                                       id=PrimaryKey(str),
                                       name=Required(str),
                                       deps=Set('ModuleDep', reverse='module'),
                                       dep_of=Set('ModuleDep', reverse='dep'),
                                       )
        self.ModuleDep = self.make_entity('ModuleDep',
                                          module=Required(self.Module),
                                          dep=Required(self.Module),
                                          visible_as=Required(str),
                                          )

    def resolve( self, iface, path ):
        objname = path.pop_str()
        if objname == ModuleList.class_name:
            return ModuleList.resolve(path)
        if objname == ModuleForm.class_name:
            return ModuleForm.resolve(path)
        if objname == ModuleDepList.class_name:
            return ModuleDepList.resolve(path)
        if objname == AvailableDepList.class_name:
            return AvailableDepList.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [
            ModuleCommand('open_module_list', 'Modules', 'Open module list', 'Alt+M', self.name),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'open_module_list':
            return request.make_response_object(ModuleList())
        return PonyOrmModule.run_command(self, request, command_id)
