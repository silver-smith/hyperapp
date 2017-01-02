import logging
import sys
from functools import partial
from types import SimpleNamespace
import abc
import importlib
import importlib.machinery
from .htypes import TypeRegistry, TypeRegistryRegistry, tModule

log = logging.getLogger(__name__)


class ModuleManager(object):

    def __init__( self, services, type_registry_registry ):
        assert isinstance(type_registry_registry, TypeRegistryRegistry), repr(type_registry_registry)
        self._services = services
        self._type_registry_registry = type_registry_registry
        self._type_modules = {}  # fullname -> ModuleType
        self._code_modules = {}  # fullname -> tModule
        self._name2code_module = {}  # name -> tModule
        self.modules = SimpleNamespace()
        self.types = SimpleNamespace()

    def register_meta_hook( self ):
        sys.meta_path.append(self)

    def unregister_meta_hook( self ):
        sys.meta_path.remove(self)

    def find_spec( self, fullname, path, target=None ):
        if fullname in self._code_modules:
            return importlib.machinery.ModuleSpec(fullname, self)
        if fullname.startswith('hyperapp.common.interface.'):
            l = fullname.split('.')
            if len(l) == 4 and self._type_registry_registry.has_type_registry(l[-1]):
                return importlib.machinery.ModuleSpec(fullname, self)

    def exec_module(self, module):
        #log.debug('exec_module: %s', module)
        code_module = self._code_modules.get(module.__name__)
        if code_module:
            self._exec_code_module(module, code_module)
            return
        if module.__name__.startswith('hyperapp.common.interface.'):
            l = module.__name__.split('.')
            if len(l) == 4 and self._type_registry_registry.has_type_registry(l[-1]):
                self._exec_type_module(module, l[-1])
            return
        assert False, repr(module.__name__)

    def _register_provided_services( self, module, module_dict ):
        pass

    def has_module( self, module_name ):
        return (module_name in self._name2code_module)

    def load_code_module( self, module, fullname=None ):
        assert isinstance(module, tModule), repr(module)
        if fullname is None:
            fullname = module.package + '.' + module.id.replace('-', '_')
        if fullname in sys.modules:
            return  # already loaded
        self._code_modules[fullname] = module
        self._name2code_module[fullname.split('.')[-1]] = module
        importlib.import_module(fullname)

    def _exec_code_module( self, module, code_module ):
        ast = compile(code_module.source, code_module.fpath, 'exec')  # using compile allows to associate file path with loaded module
        exec(ast, module.__dict__)
        self._register_provided_services(code_module, module.__dict__)
        setattr(self.modules, module.__name__.split('.')[-1], module)

    def _exec_type_module( self, module, module_name ):
        log.info('    importing type module %r', module_name)
        type_registry = self._type_registry_registry.resolve_type_registry(module_name)
        for name, t in type_registry.items():
            module.__dict__[name] = t
            log.info('        resolved type %r -> %r', name, t)
        self._type_modules[module.__name__] = module
        setattr(self.types, module.__name__.split('.')[-1], module)
