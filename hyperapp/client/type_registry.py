from ..common.util import is_list_inst, encode_path
from ..common.htypes import Interface, tTypeModule, make_meta_type_registry, builtin_type_registry, IfaceRegistry
from ..common.type_module import resolve_typedefs
from ..common import module_manager as common_module_manager


class TypeRegistry(common_module_manager.TypeModuleRegistry):

    def __init__( self, iface_registry ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        self._iface_registry = iface_registry
        self._name2module = {}  # module name -> tTypeModule
        self._class2module = {}  # encoded hierarchy_id|class_id -> tTypeModule
        self._module_name_to_type_registry = {}

    def register_all( self, type_modules ):
        assert is_list_inst(type_modules, tTypeModule), repr(type_modules)
        for type_module in type_modules:
            self.register(type_module)

    def register( self, type_module ):
        assert isinstance(type_module, tTypeModule), repr(type_module)
        self._name2module[type_module.module_name] = type_module
        for rec in type_module.provided_classes:
            self._class2module[encode_path([rec.hierarchy_id, rec.class_id])] = type_module
        self._resolve_module(type_module)

    def get_dynamic_module_id( self, id ):
        type_module = self._class2module.get(id)
        if not type_module:
            return None
        return type_module.module_name

    def has_module( self, module_name ):
        return module_name in self._name2module

    def resolve( self, module_name ):
        return self._name2module[module_name]

    def resolve_type_registry( self, module_name ):
        registry = self._module_name_to_type_registry.get(module_name)
        if registry:
            return registry
        module = self._name2module.get(module_name)
        assert module, 'Unknown type module: %r' % module_name
        return self._resolve_module(module)

    def _resolve_module( self, module ):
        registry = resolve_typedefs(make_meta_type_registry(), builtin_type_registry(), module.typedefs)
        self._module_name_to_type_registry[module.module_name] = registry
        self._register_ifaces(registry)
        return registry

    def _register_ifaces( self, type_registry ):
        for name, t in type_registry.items():
            if not isinstance(t, Interface): continue
            self._iface_registry.register(t)
