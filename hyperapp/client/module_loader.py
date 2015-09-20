import os.path
import sys
from types import ModuleType
from ..common.util import is_list_inst


CLIENT_PACKAGE = 'hyperapp.client.dynamic'
MODULES_DIR = os.path.dirname(__file__)


class ModuleDep(object):

    def __init__( self, module, visible_as ):
        assert isinstance(module, Module), repr(module)
        self.module = module
        self.visible_as = visible_as


class Module(object):

    def __init__( self, id, fpath, src, deps=None ):
        assert deps is None or is_list_inst(deps, ModuleDep), repr(deps)
        self.id = id
        self.fpath = fpath
        self.src = src  # unicode
        self.deps = deps or []

    def load( self, name ):
        if name:
            full_name = CLIENT_PACKAGE + '.' + self.id
        else:
            full_name = CLIENT_PACKAGE
        module = ModuleType(full_name, 'dynamic hyperapp module %r loaded as %r' % (self.id, name))
        sys.modules[full_name] = module
        ast = compile(self.src, self.fpath, 'exec')
        exec(ast, module.__dict__)
        return module


def load_client_module( module_id, name, fname ):
    fpath = os.path.join(MODULES_DIR, fname)
    with open(fpath) as f:
        src = f.read()
    module = Module(module_id, fpath, src)
    module.load(name)


root = Module('dynamic_module_root', '', '')
root.load(None)
sys.modules[CLIENT_PACKAGE] = root
