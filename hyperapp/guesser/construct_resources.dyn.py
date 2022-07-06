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
    type_module_loader.load_type_modules([resources_dir], custom_types)
    custom_modules = local_modules.copy()
    code_module_loader.load_code_modules(custom_types, [resources_dir], custom_modules)
    module_reg = {
        **resource_module_registry,
        **legacy_type_resource_loader(custom_types),
        **legacy_module_resource_loader(custom_modules),
        }
    resource_loader([resources_dir], module_reg)
    return module_reg


class Constructor:

    def __init__(self, root_dir, full_module_name, module_path):
        self._local_res_module_reg = custom_res_module_reg(module_path.parent)
        self.resource_module = resource_module_factory(
            resource_module_registry=self._local_res_module_reg,
            name=full_module_name,
            path=module_path.with_name(f'{module_path.name}_auto_import.resources.yaml'),
            load_from_file=False,
            )

    def on_module(self, module_name, module_path, imports):
        module_res_t = resource_type_producer(htypes.python_module.python_module)
        import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t
        for r in imports:
            if '.' in r.resource_name:
                self.resource_module.add_import(r.resource_name)
        module_def = module_res_t.definition_t(
            module_name=module_name,
            file_name=module_path.name,
            import_list=[
                import_rec_def_t(r.name, r.resource_name)
                for r in imports
                ],
            )
        module_res_name = module_name.replace('.', '_') + '_module'
        self.resource_module.set_definition(module_res_name, module_res_t, module_def)


def construct_resources(full_module_name, module_name, module_path, root_dir):
    _log.info("Construct resources from: %s", full_module_name)

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    constructor = Constructor(root_dir, full_module_name, module_path)

    custom_module_dirs = [*module_dir_list, hyperapp_dir / module_path.parent]
    with subprocess_running(custom_module_dirs, rpc_endpoint, identity, 'guesser') as process:

        visitor = ModuleVisitor(
            on_module=constructor.on_module,
            )
        visitor.run(process, module_name, module_path)

    return constructor.resource_module
