# get module ref from it's globals, with caching

from .code_module import builtin_module_t


class ModuleRefResolver:

    def __init__(self, ref_registry):
        self._ref_registry = ref_registry
        self._builtin_module_name_to_ref = {}

    def get_module_ref(self, globals):
        try:
            return globals['__module_ref__']
        except KeyError:
            pass
        module_name = globals['__name__']
        try:
            return self._builtin_module_name_to_ref[module_name]
        except KeyError:
            pass
        module_ref = self._ref_registry.register_object(builtin_module_t(module_name))
        self._builtin_module_name_to_ref[module_name] = module_ref
        return module_ref
