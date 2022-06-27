import logging

from . import htypes
from .services import (
    auto_importer_imports_ref,
    construct_global,
    mosaic,
    resource_module_factory,
    resource_type_producer,
    runner_method_collect_attributes_ref,
    subprocess_running,
    )

_log = logging.getLogger(__name__)


def construct_resources(module_name, module_path, root_dir):
    _log.info("Construct resources from: %s", module_name)
    module_last_name = module_name.split('.')[-1]
    module_res_name = f'{module_last_name}_module'

    resource_module = resource_module_factory(
        module_name, root_dir / f'{module_path}_auto_import.resources.yaml', load_from_file=False)

    module_res_t = resource_type_producer(htypes.python_module.python_module)
    import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t

    ai_module_def = module_res_t.definition_t(
        module_name=module_name,
        file_name=module_path.name,
        import_list=[
            import_rec_def_t('*', 'guesser.auto_importer.auto_importer_loader'),
            ],
        )
    resource_module.set_definition(module_res_name, module_res_t, ai_module_def)
    resource_module.add_import('guesser.auto_importer.auto_importer_loader')
    ai_module = resource_module[module_res_name]
    ai_module_ref = mosaic.put(ai_module)

    with subprocess_running('guesser') as process:
        collect_attributes_call = process.rpc_call(runner_method_collect_attributes_ref)
        global_list = collect_attributes_call(ai_module_ref)
        _log.info("Collected global list: %s", global_list)

        for globl in global_list:
            construct_global(root_dir, module_name, resource_module, process, module_res_name, globl)

        auto_importer_imports_call = process.rpc_call(auto_importer_imports_ref)
        imports = auto_importer_imports_call()
        _log.info("Import list: %s", imports)

    resource_module.remove_import('guesser.auto_importer.auto_importer_loader')
    for r in imports:
        if '.' in r.resource_name:
            resource_module.add_import(r.resource_name)

    module_def = module_res_t.definition_t(
        module_name=module_name,
        file_name=module_path.name,
        import_list=[
            import_rec_def_t(r.name, r.resource_name)
            for r in imports
            ],
        )
    resource_module.set_definition(module_res_name, module_res_t, module_def)

    return resource_module
