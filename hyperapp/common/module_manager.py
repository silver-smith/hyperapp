import logging
import sys
from functools import partial
from types import ModuleType
import abc
from .htypes import TypeRegistry, tModule

log = logging.getLogger(__name__)


class TypeModuleRegistry(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def has_module( self, module_name ):
        pass

    # must return TypeRegistry
    @abc.abstractmethod
    def resolve_type_registry( self, module_name ):
        pass


class ModuleManager(object):

    def __init__( self, services, type_module_registry ):
        assert isinstance(type_module_registry, TypeModuleRegistry), repr(type_module_registry)
        self._services = services
        self._type_module_registry = type_module_registry
        self._type_modules = {}  # module name -> ModuleType

    def _load_module( self, module, name=None ):
        assert isinstance(module, tModule), repr(module)
        if name is None:
            name = module.package + '.' + module.id.replace('-', '_')
        if name in sys.modules:
            return  # already loaded
        module_inst = ModuleType(name, 'dynamic hyperapp module %r loaded as %r' % (module.id, name))
        sys.modules[name] = module_inst
        ast = compile(module.source, module.fpath, 'exec')  # using compile allows to associate file path with loaded module
        module_inst.__dict__['__builtins__'] = self._make_builtins_module(name)
        exec(ast, module_inst.__dict__)
        self._register_provided_services(module, module_inst.__dict__)
        return module_inst

    def _register_provided_services( self, module, module_dict ):
        pass

    def _make_builtins_module( self, module_name ):
        builtins = ModuleType('builtins', 'Custom hyperapp builtins module')
        builtins.__dict__.update(__builtins__)
        builtins.__dict__['__import__'] = partial(self._import, module_name)
        return builtins

    def _import( self, module_name, name, globals=None, locals=None, from_list=(), level=0 ):
        ## log.info('__import__ %r - %r %r %r %r %r', module_name, name, from_list, level, globals, locals)
        if level == 1 and '.' not in name and self._type_module_registry.has_module(name):
            result = self._import_type_module(name)
        else:
            result = __import__(name, globals, locals, from_list, level)
            for sub_name in from_list or []:
                ## print('  sub_name', sub_name, hasattr(result, sub_name), self._type_module_registry.has_module(sub_name))
                if hasattr(result, sub_name): continue
                if self._type_module_registry.has_module(sub_name):
                    setattr(result, sub_name, self._import_type_module(sub_name))
        ## log.info('  -> %r', result)
        return result

    def _import_type_module( self, module_name ):
        log.info('importing type module %r', module_name)
        if module_name in self._type_modules:
            return self._type_modules[module_name]
        type_registry = self._type_module_registry.resolve_type_registry(module_name)
        module = ModuleType('hyperapp.client.%s' % module_name, 'Hyperapp type module %s' % module_name)
        for name, t in type_registry.items():
            module.__dict__[name] = t
            log.info('    resolved type %r -> %r', name, t)
        self._type_modules[module_name] = module
        return module
