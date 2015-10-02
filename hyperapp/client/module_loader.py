import os.path
import sys
from types import ModuleType
from ..common.util import is_list_inst
from ..common.packet_container import Module


def load_client_module( module, name=None ):
    if name is None:
        name = module.package + '.' + module.id.replace('-', '_')
    name = str(name)  # python expects name and package to be a an str, assume it is
    if name in sys.modules:
        return  # already loaded
    module_inst = ModuleType(name, 'dynamic hyperapp module %r loaded as %r' % (module.id, name))
    sys.modules[name] = module_inst
    ast = compile(module.source, module.fpath, 'exec')  # compile allows to associate file path with loaded module
    exec(ast, module_inst.__dict__)
    return module_inst
