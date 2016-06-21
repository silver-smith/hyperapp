from pony.orm import db_session, commit, Required, Optional, Set, select
from ..common.identity import PublicKey
from ..common.interface.admin import user_list_iface
from .module import ModuleCommand
from .ponyorm_module import PonyOrmModule
from .object import SmallListObject


MODULE_NAME = 'admin'


class UserList(SmallListObject):

    iface = user_list_iface
    class_name = 'user_list'
    objimpl_id = 'proxy_list'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        path.check_empty()
        return cls()

    @classmethod
    def get_path( cls ):
        return this_module.make_path(cls.class_name)

    def __init__( self ):
        SmallListObject.__init__(self)

    @db_session
    def fetch_all_elements( self ):
        return list(map(self.rec2element, this_module.User.select()))

    @classmethod
    def rec2element( cls, rec ):
        commands = []
        public_key = PublicKey.from_pem(rec.public_key_pem)
        return cls.Element(cls.Row(rec.id, rec.user_name, public_key.get_short_id_hex()), commands)

    def process_request( self, request ):
        if request.command_id == 'add':
            return self.run_command_add(request)
        return SmallListObject.process_request(self, request)

    def run_command_add( self, request ):
        public_key = PublicKey.from_der(request.params.public_key_der)
        rec = this_module.User(user_name=request.params.user_name,
                               public_key_pem=public_key.to_pem())
        commit()  # make rec.id
        diff = self.Diff_add_one(self.rec2element(rec))
        subscription.distribute_update(self.iface, self.get_path(), diff)
        return self.ListHandle(self, key=rec.id)


class ThisModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.User = self.make_entity('User',
                                     user_name=Required(str),
                                     public_key_pem=Required(str),
                                     )

    def resolve( self, iface, path ):
        objname = path.pop_str()
        if objname == UserList.class_name:
            return UserList.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [
            ModuleCommand('user_list', 'User list', 'Open user list', 'Alt+U', self.name),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'user_list':
            return request.make_response_handle(UserList())
        return PonyOrmModule.run_command(self, request, command_id)


this_module = ThisModule()
