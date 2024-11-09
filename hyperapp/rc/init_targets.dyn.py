from hyperapp.common.htypes import Type
from hyperapp.resource.resource_module import AUTO_GEN_LINE

from .services import (
    code_registry_ctr,
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
from .code.config_resource_target import ConfigResourceTarget


def ctr_from_template_creg(config):
    return code_registry_ctr('ctr_from_template_creg', config)


def add_core_items(config_ctl, ctr_from_template_creg, system_config_template, target_set):
    for service_name, config in system_config_template.items():
        ctl = config_ctl[service_name]
        for key, value in config.items():
            if type(key) is not str:
                assert isinstance(key, Type)
                key = f'{key.module_name}_{key.name}'
            item_piece = ctl.item_piece(value)
            ctr = ctr_from_template_creg.animate(item_piece)
            module_name, var_name = resource_registry.reverse_resolve(item_piece)
            resource_tgt = target_set.factory.python_module_resource_by_module_name(module_name)
            assert isinstance(resource_tgt, ManualPythonModuleResourceTarget)
            ready_tgt = target_set.factory.config_item_ready(service_name, key)
            resolved_tgt = target_set.factory.config_item_resolved(service_name, key)
            complete_tgt = target_set.factory.config_item_complete(service_name, key)
            ready_tgt.set_provider(resource_tgt, target_set)
            resolved_tgt.resolve(ctr)
            complete_tgt.update_status()


def init_targets(config_ctl, ctr_from_template_creg, system_config_template, root_dir, target_set, build):
    custom_resource_registry = create_custom_resource_registry(build)
    all_imports_known_tgt = AllImportsKnownTarget()
    target_set.add(all_imports_known_tgt)
    config_tgt = ConfigResourceTarget(custom_resource_registry, resource_dir=root_dir, module_name='config', path='config.resources.yaml')
    target_set.add(config_tgt)
    for src in build.python_modules:
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
                continue
        alias_tgt = ImportTargetAlias(src, custom_resource_registry, build.types)
        import_tgt = ImportTarget(target_set, src, build.types, alias_tgt, config_tgt)
        alias_tgt.set_import_target(import_tgt)
        all_imports_known_tgt.add_import_target(import_tgt)
        target_set.add(import_tgt)
        target_set.add(alias_tgt)
    all_imports_known_tgt.init_completed()
    target_set.update_deps_for(all_imports_known_tgt)
    add_core_items(config_ctl, ctr_from_template_creg, system_config_template, target_set)
