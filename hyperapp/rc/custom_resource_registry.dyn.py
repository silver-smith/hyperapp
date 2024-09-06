from . import htypes
from .services import (
    builtin_service_resource_loader,
    builtin_types_as_dict,
    legacy_type_resource_loader,
    local_types,
    resource_registry_factory,
    type_module_loader,
    )


def _type_sources_to_type_dict(type_src_list):
    custom_types = {}
    for src in type_src_list:
        name_to_type = custom_types.setdefault(src.module_name, {})
        name_to_type[src.name] = src.type_piece
    return custom_types


def _add_legacy_types_to_cache(res_reg, legacy_type_modules):
    for module_name, module in legacy_type_modules.items():
        for var_name in module:
            res_reg.add_to_cache((module_name, var_name), module[var_name])


def create_custom_resource_registry(type_src_list):
    res_reg = resource_registry_factory()
    custom_types = _type_sources_to_type_dict(type_src_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    _add_legacy_types_to_cache(res_reg, legacy_type_modules)
    res_reg.update_modules(legacy_type_modules)
    res_reg.set_module('builtins', builtin_service_resource_loader(res_reg))
    return res_reg
