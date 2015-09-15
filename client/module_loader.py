import os.path
import sys
from types import ModuleType
from common.util import is_list_inst


CLIENT_PACKAGE = 'client.dynamic'
MODULES_DIR = os.path.dirname(__file__)


class ModuleDep(object):

    def __init__( self, module, visible_as ):
        assert isinstance(module, Module), repr(module)
        self.module = module
        self.visible_as = visible_as


class Module(object):

    def __init__( self, id, fname, src, deps=None ):
        assert deps is None or is_list_inst(deps, ModuleDep), repr(deps)
        self.id = id
        self.fname = fname
        self.src = src  # unicode
        self.deps = deps or []

    def load( self, name ):
        if name:
            full_name = CLIENT_PACKAGE + '.' + self.id
        else:
            full_name = CLIENT_PACKAGE
        module = ModuleType(full_name, 'dynamic hyperapp module %r loaded as %r' % (self.id, name))
        sys.modules[full_name] = module
        ast = compile(self.src, os.path.join(MODULES_DIR, self.fname), 'exec')
        exec(ast, module.__dict__)
        return module


def load_src( fname ):
    with open(os.path.join(MODULES_DIR, fname)) as f:
        return f.read()

def test():
    root = Module('dynamic_module_root', '', '')
    root.load(None)
    sys.modules[CLIENT_PACKAGE] = root
    form = Module('form_module_id', 'form.py', load_src('form.py'))
    form.load('form')

test()
