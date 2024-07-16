from hyperapp.resource.resource_module import AUTO_GEN_LINE

from .code.custom_resource_registry import create_custom_resource_registry
from .code.python_module_resource_target import ManualPythonModuleResourceTarget
from .code.import_target import (
    AllImportsKnownTarget,
    ImportTargetAlias,
    ImportTarget,
    )


def add_common_mark_services(resource_tgt, target_factory):
    service_found_tgt = target_factory.service_found('mark')
    service_complete_tgt = target_factory.service_complete('mark')
    service_found_tgt.set_provider(resource_tgt, attr_name='mark')
    service_complete_tgt.update_status()


def init_targets(root_dir, target_set, python_module_src_list, type_src_list):
    custom_resource_registry = create_custom_resource_registry(root_dir)
    all_imports_known_tgt = AllImportsKnownTarget()
    for src in python_module_src_list:
        if root_dir.joinpath(src.resource_path).read_text().startswith(AUTO_GEN_LINE):
            alias_tgt = ImportTargetAlias(src, custom_resource_registry, type_src_list)
            import_tgt = ImportTarget(src, type_src_list, alias_tgt)
            all_imports_known_tgt.add_import_target(import_tgt)
            target_set.add(import_tgt)
            target_set.add(alias_tgt)
        else:
            resource_tgt = ManualPythonModuleResourceTarget(src, custom_resource_registry)
            target_set.add(resource_tgt)
            if src.name == 'common.mark':
                add_common_mark_services(resource_tgt, target_set.factory)
    target_set.add(all_imports_known_tgt)
