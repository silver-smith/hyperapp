import logging
from ..common.htypes import (
    make_meta_type_registry,
    builtin_type_registry,
    )
from ..common import module_manager as common_module_manager
from .registry import DynamicModuleRegistryProxy

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__( self, services ):
        common_module_manager.ModuleManager.__init__(self, services, services.type_module_registry)
        self._id2module = {}
        self._objimpl_registry = services.objimpl_registry
        self._view_registry = services.view_registry
        self._meta_type_registry = make_meta_type_registry()
        self._builtin_type_registry = builtin_type_registry()

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
            if self._type_module_registry.has_module(id): continue  # do not return type modules
            module = self._id2module[id]
            modules.append(module)
        return modules

    def _register_provided_services( self, module, module_dict ):
        register_object_implementations = module_dict.get('register_object_implementations')
        if register_object_implementations:
            register_object_implementations(DynamicModuleRegistryProxy(self._objimpl_registry, module.id), self._services)
        register_views = module_dict.get('register_views')
        if register_views:
            register_views(DynamicModuleRegistryProxy(self._view_registry, module.id), self._services)
