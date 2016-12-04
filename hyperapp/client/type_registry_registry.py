import logging
from ..common.util import is_list_inst, encode_path
from ..common import htypes
from ..common.htypes import Interface, tTypeModule, make_meta_type_registry, builtin_type_registry, IfaceRegistry, TypeResolver
from ..common.type_module import resolve_typedefs
from ..common import module_manager as common_module_manager

log = logging.getLogger(__name__)


class TypeRegistryRegistry(htypes.TypeRegistryRegistry):

    def __init__( self, iface_registry ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        htypes.TypeRegistryRegistry.__init__(self)
        self._iface_registry = iface_registry
        self._name2module = {}  # module name -> tTypeModule
        self._class2module = {}  # encoded hierarchy_id|class_id -> tTypeModule
        self._iface2module = {}  # iface_id -> tTypeModule
        self._module_name_to_type_registry = {}

    def register_all( self, type_modules ):
        assert is_list_inst(type_modules, tTypeModule), repr(type_modules)
        for type_module in type_modules:
            self.register(type_module)

    def register( self, type_module ):
        assert isinstance(type_module, tTypeModule), repr(type_module)
        log.info('type module registry: registering type module %r', type_module.module_name)
        self._name2module[type_module.module_name] = type_module
        for rec in type_module.provided_classes:
            self._class2module[encode_path([rec.hierarchy_id, rec.class_id])] = type_module
        self._resolve_module_typedefs(type_module)

    def get_class_dynamic_module_id( self, id ):
        type_module = self._class2module.get(id)
        if type_module:
            return type_module.module_name
        else:
            return None

    def get_iface_dynamic_module_id( self, id ):
        type_module = self._iface2module.get(id)
        if type_module:
            return type_module.module_name
        else:
            return None

    def has_module( self, module_name ):
        return module_name in self._name2module

    def resolve( self, module_name ):
        return self._name2module[module_name]

    def has_type_registry( self, module_name ):
        return module_name in self._module_name_to_type_registry

    def resolve_type_registry( self, module_name ):
        registry = self._module_name_to_type_registry.get(module_name)
        if registry:
            return registry
        module = self._name2module.get(module_name)
        assert module, 'Unknown type module: %r' % module_name
        return self._resolve_module_typedefs(module)

    def _resolve_module_typedefs( self, module ):
        resolver = TypeResolver([builtin_type_registry()] + list(self._module_name_to_type_registry.values()))
        type_registry = resolve_typedefs(make_meta_type_registry(), resolver, module.typedefs)
        self._module_name_to_type_registry[module.module_name] = type_registry
        self._register_ifaces(module, type_registry)
        return type_registry

    def _register_ifaces( self, module, type_registry ):
        for name, t in type_registry.items():
            if not isinstance(t, Interface): continue
            self._iface_registry.register(t)
            self._iface2module[name] = module
