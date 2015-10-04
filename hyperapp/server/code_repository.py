from . import module
from ..common.interface.code_repository import (
    ModuleDep,
    Module,
    code_repository_iface,
    )


MODULE_NAME = 'code_repository'


class CodeRepositoryModule(module.Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)


module = CodeRepositoryModule()
