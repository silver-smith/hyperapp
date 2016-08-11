import os.path
import sys
import logging
from types import ModuleType
from functools import partial
from ..common.util import is_list_inst
from ..common.htypes import (
    make_meta_type_registry,
    builtin_type_registry,
    )
from .registry import DynamicModuleRegistryProxy

log = logging.getLogger(__name__)


class ModuleManager(object):

    def __init__( self, services ):
        self._id2module = {}
        self._services = services
        self._type_registry = services.type_registry
        self._objimpl_registry = services.objimpl_registry
        self._view_registry = services.view_registry
        self._meta_type_registry = make_meta_type_registry()
        self._builtin_type_registry = builtin_type_registry()
        self._type_modules = {}  # module name -> ModuleType

    def add_modules( self, modules ):
        for module in modules:
            self.add_module(module)

    def add_module( self, module ):
        log.info('-- loading module %r package=%r fpath=%r', module.id, module.package, module.fpath)
        self._id2module[module.id] = module
        self._load_module(module)

    def resolve_ids( self, module_ids ):
        modules = []
        for id in module_ids:
            modules.append(self._id2module[id])
        return modules

    def _load_module( self, module, name=None ):
        if name is None:
            name = module.package + '.' + module.id.replace('-', '_')
        if name in sys.modules:
            return  # already loaded
        module_inst = ModuleType(name, 'dynamic hyperapp module %r loaded as %r' % (module.id, name))
        sys.modules[name] = module_inst
        ast = compile(module.source, module.fpath, 'exec')  # compile allows to associate file path with loaded module
        module_inst.__dict__['__builtins__'] = self._make_builtins_module(name)
        exec(ast, module_inst.__dict__)
        self._register_provided_services(module, module_inst.__dict__)
        return module_inst

    def _register_provided_services( self, module, module_dict ):
        register_object_implementations = module_dict.get('register_object_implementations')
        if register_object_implementations:
            register_object_implementations(DynamicModuleRegistryProxy(self._objimpl_registry, module.id), self._services)
        register_views = module_dict.get('register_views')
        if register_views:
            register_views(DynamicModuleRegistryProxy(self._view_registry, module.id), self._services)

    def _make_builtins_module( self, module_name ):
        builtins = ModuleType('builtins', 'Custom hyperapp builtins module')
        builtins.__dict__.update(__builtins__)
        builtins.__dict__['__import__'] = partial(self._import, module_name)
        return builtins

    def _import( self, module_name, name, globals=None, locals=None, from_list=(), level=0 ):
        log.info('__import__ %r - %r %r %r %r %r', module_name, name, from_list, level, globals, locals)
        if level == 1 and '.' not in module_name and self._type_registry.has_module(module_name):
            result = self._import_type_module(module_name)
        else:
            result = __import__(name, globals, locals, from_list, level)
        log.info('  -> %r', result)
        return result

    def _import_type_module( self, module_name ):
        log.info('importing type module %r', module_name)
        if module_name in self._type_modules:
            return self._type_modules[module_name]
        type_module = self._type_module.resolve(module_name)
        module = ModuleType('hyperapp.client.%s' % module_name, 'Hyperapp type module %s' % module_name)
        for typedef in type_module.typedefs:
            t = self._meta_type_registry.resolve(self._builtin_type_registry, typedef.type)
            module.__dict__[typedef.name] = t
            log.info('    resolved type %r -> %r', typedef.name, t)
        self._type_modules[module_name] = module
        return module
