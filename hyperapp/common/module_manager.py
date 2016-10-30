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
        name_list = list(filter(None, name.split('.')))  # remove possible empty name at the end
        module_name_list = module_name.split('.')
        if level:
            full_name_list = module_name_list[:len(module_name_list) - level] + name_list
        else:
            full_name_list = name_list
        log.debug('%r %r %r %r %r', module_name, level, name, full_name_list, from_list)
        module = self._import_module(full_name_list, globals, locals)
        for sub_name in from_list or []:
            log.debug('  %r : %r %r', sub_name, module, hasattr(module, sub_name))
            if hasattr(module, sub_name): continue
            sub_module = self._import_module(full_name_list + [sub_name], globals, locals)
            setattr(module, sub_name, sub_module)
        ## log.info('  -> %r', result)
        return module

    def _import_module( self, name_list, globals, locals ):
        if (name_list[:3] == ['hyperapp', 'common', 'interface']
            and len(name_list) == 4
            and self._type_module_registry.has_module(name_list[3])):
            return self._import_type_module(name_list[3])
        module = __import__('.'.join(name_list), globals, locals, (), 0)
        return module
        for name in name_list[1:]:  # __import__ returns top-level module
            module = getattr(module, name)
        return module

    def _import_type_module( self, module_name ):
        log.info('    importing type module %r', module_name)
        if module_name in self._type_modules:
            return self._type_modules[module_name]
        type_registry = self._type_module_registry.resolve_type_registry(module_name)
        module = ModuleType('hyperapp.client.%s' % module_name, 'Hyperapp type module %s' % module_name)
        for name, t in type_registry.items():
            module.__dict__[name] = t
            log.info('        resolved type %r -> %r', name, t)
        self._type_modules[module_name] = module
        return module
