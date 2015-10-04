from ..common.interface.code_repository import (
    ModuleDep,
    Module,
    code_repository_iface,
    )
from . import module as module_mod
from .object import Object


MODULE_NAME = 'code_repository'



class CodeRepository(Object):

    iface = code_repository_iface
    class_name = 'code_repository'

    @classmethod
    def resolve( cls, path ):
        path.check_empty()
        return cls()

    @classmethod
    def get_path( cls ):
        return module.make_path(cls.class_name)

    def process_request( self, request ):
        if request.command_id == 'get_modules':
            return self.run_command_get_modules(request)
        return Object.process_request(self, request)

    def run_command_get_modules( self, request ):
        print 'run_command_get_modules', request.module_ids


class CodeRepositoryModule(module_mod.Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == CodeRepository.class_name:
            return CodeRepository.resolve(path)
        path.raise_not_found()


module = CodeRepositoryModule()
