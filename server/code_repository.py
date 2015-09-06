from pony.orm import db_session, commit, desc, PrimaryKey, Required, Set
from .ponyorm_module import PonyOrmModule


MODULE_NAME = 'code_repository'


class CodeRepositoryModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2( self ):
        self.Module = self.make_entity('Module',
                                       id=PrimaryKey(unicode),
                                       name=Required(unicode),
                                       )


module = CodeRepositoryModule()
