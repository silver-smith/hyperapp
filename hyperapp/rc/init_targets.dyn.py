from hyperapp.resource.resource_module import AUTO_GEN_LINE

from .services import (
    code_registry_ctr2,
    resource_registry,
    web,
    )
from .code.custom_resource_registry import create_custom_resource_registry
from .code.python_module_resource_target import ManualPythonModuleResourceTarget
from .code.import_target import (
    AllImportsKnownTarget,
    ImportTargetAlias,
    ImportTarget,
    )
from .code.service_ctr import ServiceCtr
from .code.config_resource_target import ConfigResourceTarget


def ctr_from_template_creg(config):
    return code_registry_ctr2('ctr-from-template', config)


def add_common_mark_services(resource_tgt, target_set):
    service_found_tgt = target_set.factory.service_found('mark')
    service_resolved_tgt = target_set.factory.service_resolved('mark')
    service_complete_tgt = target_set.factory.service_complete('mark')
    ctr = ServiceCtr('mark', 'mark')
    service_found_tgt.set_provider(resource_tgt, ctr, target_set)
    service_resolved_tgt.resolve(ctr)
    service_resolved_tgt.update_status()
    service_complete_tgt.update_status()


def add_core_items(cfg_item_creg, ctr_from_template_creg, system_config, target_set):
    for sc in system_config.services:
        for item_ref in sc.items:
            item_piece = web.summon(item_ref)
            item = cfg_item_creg.animate(item_piece, sc.service)
            ctr = ctr_from_template_creg.animate(item_piece)
            module_name, var_name = resource_registry.reverse_resolve(item_piece)
            resource_tgt = target_set.factory.python_module_resource_by_module_name(module_name)
            assert isinstance(resource_tgt, ManualPythonModuleResourceTarget)
            ready_tgt = target_set.factory.config_item_ready(sc.service, item.key)
            resolved_tgt = target_set.factory.config_item_resolved(sc.service, item.key)
            complete_tgt = target_set.factory.config_item_complete(sc.service, item.key)
            ready_tgt.set_provider(resource_tgt, target_set)
            resolved_tgt.resolve(ctr)
            complete_tgt.update_status()


def init_targets(cfg_item_creg, ctr_from_template_creg, system_config, root_dir, target_set, python_module_src_list, type_src_list):
    custom_resource_registry = create_custom_resource_registry(root_dir)
    all_imports_known_tgt = AllImportsKnownTarget()
    target_set.add(all_imports_known_tgt)
    config_tgt = ConfigResourceTarget(custom_resource_registry, resource_dir=root_dir, module_name='config', path='config.resources.yaml')
    target_set.add(config_tgt)
    for src in python_module_src_list:
        try:
            resource_text = root_dir.joinpath(src.resource_path).read_text()
        except FileNotFoundError:
            pass
        else:
            if not resource_text.startswith(AUTO_GEN_LINE):
                resource_dir = root_dir / src.path.parent
                resource_tgt = ManualPythonModuleResourceTarget(
                    src, custom_resource_registry, resource_dir, resource_text)
                target_set.add(resource_tgt)
                if src.name == 'common.mark':
                    add_common_mark_services(resource_tgt, target_set)
                continue
        alias_tgt = ImportTargetAlias(src, custom_resource_registry, type_src_list)
        import_tgt = ImportTarget(src, type_src_list, alias_tgt)
        alias_tgt.set_import_target(import_tgt)
        all_imports_known_tgt.add_import_target(import_tgt)
        target_set.add(import_tgt)
        target_set.add(alias_tgt)
    all_imports_known_tgt.init_completed()
    target_set.update_deps_for(all_imports_known_tgt)
    add_core_items(cfg_item_creg, ctr_from_template_creg, system_config, target_set)
