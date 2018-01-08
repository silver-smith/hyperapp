import logging
import sys
from functools import partial
from types import SimpleNamespace
import abc
import importlib
import importlib.machinery
from .htypes import TypeRegistry, TypeRegistryRegistry
from .module_registry import ModuleRegistry
from .type_module_repository import TYPE_MODULES_PACKAGE

log = logging.getLogger(__name__)


class ModuleManager(object):

    def __init__(self, services, type_registry_registry, module_registry):
        assert isinstance(type_registry_registry, TypeRegistryRegistry), repr(type_registry_registry)
        assert isinstance(module_registry, ModuleRegistry), repr(module_registry)
        self._services = services
        self._type_registry_registry = type_registry_registry
        self._module_registry = module_registry
        self._type_modules = {}  # fullname -> ModuleType
        self._code_modules = {}  # fullname -> tModule
        self._name2code_module = {}  # name -> tModule
        self.modules = SimpleNamespace()

    def register_meta_hook(self):
        sys.meta_path.append(self)

    def unregister_meta_hook(self):
        sys.meta_path.remove(self)

    def find_spec(self, fullname, path, target=None):
        if fullname in self._code_modules:
            return importlib.machinery.ModuleSpec(fullname, self)
        if fullname.startswith(TYPE_MODULES_PACKAGE + '.'):
            l = fullname.split('.')
            if len(l) == 4 and self._type_registry_registry.has_type_registry(l[-1]):
                return importlib.machinery.ModuleSpec(fullname, self)

    def exec_module(self, module):
        # log.debug('    exec_module: %s', module)
        code_module = self._code_modules.get(module.__name__)
        if code_module:
            self._exec_code_module(module, code_module)
            return
        if module.__name__.startswith(TYPE_MODULES_PACKAGE + '.'):
            l = module.__name__.split('.')
            if len(l) == 4 and self._type_registry_registry.has_type_registry(l[-1]):
                self._exec_type_module(module, l[-1])
            return
        assert False, repr(module.__name__)

    def _register_provided_services(self, module, module_dict):
        this_module_class = module_dict.get('ThisModule')
        if this_module_class:
            this_module = this_module_class(self._services)
            module_dict['this_module'] = this_module
            self._module_registry.register(this_module)

    def has_module(self, module_name):
        return (module_name in self._name2code_module)

    def load_code_module_list(self, module_list):
        for module in module_list:
            self.load_code_module(module)

    def load_code_module(self, module, fullname=None):
        log.info('-- loading module %r package=%r fpath=%r', module.id, module.package, module.fpath)
        #assert isinstance(module, self._packet_types.module), repr(module)
        if fullname is None:
            fullname = module.package + '.' + module.id.replace('-', '_')
        self._code_modules[fullname] = module
        self._name2code_module[fullname.split('.')[-1]] = module
        if fullname in sys.modules:  # already loaded
            importlib.reload(sys.modules[fullname])
        else:
            importlib.import_module(fullname)

    def _exec_code_module(self, module, code_module):
        log.info('   executing code module %r package=%r fpath=%r', code_module.id, code_module.package, code_module.fpath)
        ast = compile(code_module.source, code_module.fpath, 'exec')  # using compile allows to associate file path with loaded module
        exec(ast, module.__dict__)
        self._register_provided_services(code_module, module.__dict__)
        setattr(self.modules, module.__name__.split('.')[-1], module)

    def _exec_type_module(self, module, module_name):
        log.info('    executing type module %r', module_name)
        type_registry = self._type_registry_registry.resolve_type_registry(module_name)
        for name, t in type_registry.items():
            module.__dict__[name] = t
            log.info('        resolved type %r -> %r', name, t)
        self._type_modules[module.__name__] = module
