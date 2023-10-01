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


RcContext = namedtuple('RcContext', 'resource_registry types type_recorder_res_list')


def _load_legacy_type_resources(dir_list):
    custom_types = {
        **builtin_types_as_dict(),
        **local_types,
        }

    type_module_loader.load_type_modules(dir_list, custom_types)

    resource_list = []
    for module_name, type_module in custom_types.items():
        for name, type_ref in type_module.items():
            resource = htypes.builtin.legacy_type(type_ref)
            resource_ref = mosaic.put(resource)
            resource_list.append(
                htypes.import_recorder.resource(('htypes', module_name, name), resource_ref))
    return (custom_types, resource_list)


def _add_legacy_types_to_cache(res_reg, legacy_type_modules):
    for module_name, module in legacy_type_modules.items():
        for var_name in module:
            res_reg.add_to_cache((module_name, var_name), module[var_name])


def create_custom_resource_registry(root_dir, dir_list):
    res_reg = resource_registry_factory()

    custom_types, type_recorder_res_list = _load_legacy_type_resources(dir_list)
    legacy_type_modules = legacy_type_resource_loader(custom_types)
    _add_legacy_types_to_cache(res_reg, legacy_type_modules)
    res_reg.update_modules(legacy_type_modules)

    res_reg.set_module('builtin_service', builtin_service_resource_loader(res_reg))

    return RcContext(
        resource_registry=res_reg,
        types=custom_types,
        type_recorder_res_list=type_recorder_res_list,
        )
