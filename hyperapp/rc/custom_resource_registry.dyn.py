from collections import namedtuple

from . import htypes
from .services import (
    builtin_service_resource_loader,
    builtin_types_as_dict,
    legacy_type_resource_loader,
    local_types,
    mosaic,
    resource_registry_factory,
    type_module_loader,
    )


RcContext = namedtuple('RcContext', 'resource_registry types type_recorder_res_list type_pair_to_resource')


def _load_legacy_type_resources(dir_list):
    custom_types = {
        **builtin_types_as_dict(),
        **local_types,
        }

    type_module_loader.load_type_modules(dir_list, custom_types)

    resource_list = []
    pair_to_resource = {}
    for module_name, type_module in custom_types.items():
        for name, type_piece in type_module.items():
            resource_ref = mosaic.put(type_piece)
            resource_list.append(
                htypes.import_recorder.resource(('htypes', module_name, name), resource_ref))
            pair_to_resource[module_name, name] = type_piece
    return (custom_types, resource_list, pair_to_resource)


def _add_legacy_types_to_cache(res_reg, legacy_type_modules):
    for module_name, module in legacy_type_modules.items():
        for var_name in module:
            res_reg.add_to_cache((module_name, var_name), module[var_name])


def create_custom_resource_registry(root_dir, dir_list):
    res_reg = resource_registry_factory()

    custom_types, type_recorder_res_list, pair_to_resource = _load_legacy_type_resources(dir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    _add_legacy_types_to_cache(res_reg, legacy_type_modules)
    res_reg.update_modules(legacy_type_modules)

    res_reg.set_module('builtins', builtin_service_resource_loader(res_reg))

    return RcContext(
        resource_registry=res_reg,
        types=custom_types,
        type_recorder_res_list=type_recorder_res_list,
        type_pair_to_resource=pair_to_resource,
        )
