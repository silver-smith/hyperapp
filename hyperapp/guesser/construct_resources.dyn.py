import logging

from . import htypes
from .services import (
    auto_importer_imports_ref,
    construct_global,
    endpoint_registry,
    code_module_loader,
    generate_rsa_identity,
    hyperapp_dir,
    legacy_module_resource_loader,
    legacy_type_resource_loader,
    local_modules,
    local_types,
    module_dir_list,
    mosaic,
    resource_loader,
    resource_module_factory,
    resource_module_registry,
    resource_type_producer,
    rpc_endpoint_factory,
    runner_method_collect_attributes_ref,
    subprocess_running,
    type_module_loader,
    )
from .module import ModuleVisitor

_log = logging.getLogger(__name__)


def custom_res_module_reg(resources_dir):
    custom_types = {**local_types}
    type_module_loader.load_type_modules([hyperapp_dir / resources_dir], custom_types)
    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [hyperapp_dir / resources_dir], custom_modules)
    module_reg = {
        **resource_module_registry,
        **legacy_type_resource_loader(custom_types),
        **legacy_module_resource_loader(custom_modules),
        }
    resource_loader([hyperapp_dir / resources_dir], module_reg)
    return module_reg


def construct_resources(full_module_name, module_name, module_path, root_dir):
    _log.info("Construct resources from: %s", full_module_name)

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    custom_module_dirs = [*module_dir_list, hyperapp_dir / module_path.parent]
    with subprocess_running(custom_module_dirs, rpc_endpoint, identity, 'guesser') as process:

        visitor = ModuleVisitor()
        visitor.run(process, module_name, module_path)
