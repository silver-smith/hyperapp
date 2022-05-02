import logging
from collections import defaultdict

from hyperapp.common.code_module import code_module_t
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class LegacyModuleResourceModule:

    def __init__(self):
        self._name_to_piece = {}  # Full module name -> code_module_t ref

    @property
    def name(self):
        return 'legacy_module'

    def add(self, name, code_module_ref):
        self._name_to_piece[name] = code_module_ref

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)

    @property
    def associations(self):
        return set()


def make_legacy_module_resource_modules(local_modules):
    name_to_module = defaultdict(LegacyModuleResourceModule)
    for name, code_module in local_modules.by_name.items():
        *module_name_parts, var_name = name.split('.')
        module_name = '.'.join(['legacy_module', *module_name_parts])
        name_to_module[module_name].add(var_name, code_module)
        log.info("Legacy module resource %s.%s: %s", module_name, var_name, code_module)
    return name_to_module


def python_object(piece, module_registry, module_by_requirement, services):
    if not module_registry.module_loaded(piece):
        module_registry.import_module_list(services, [piece], module_by_requirement, config_dict={})
    return module_registry.get_python_module(piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_registry.update(make_legacy_module_resource_modules(services.local_modules))
        services.python_object_creg.register_actor(
            code_module_t, python_object, services.module_registry, services.local_modules.by_requirement, services)
