from pathlib import Path

from hyperapp.boot.htypes import Type
from hyperapp.boot.resource.resource_module import AUTO_GEN_LINE

from .services import (
    code_registry_ctr,
    hyperapp_dir,
    )
from .code.target_set import TargetSet
from .code.python_src import PythonModuleSrc
from .code.python_module_resource_target import ManualPythonModuleResourceTarget
from .code.import_target import (
    AllImportsKnownTarget,
    ImportTarget,
    )
from .code.config_resource_target import ConfigResourceTarget
from .code.cfg_item_req import CfgItemReq
from .code.service_req import ServiceReq
from .code.marker_req import MarkerReq


def ctr_from_template_creg(config):
    return code_registry_ctr('ctr_from_template_creg', config)


def add_base_target_items(config_ctl, ctr_from_template_creg, base_config_templates, target_set, project):
    for service_name, config in base_config_templates.items():
        ctl = config_ctl[service_name]
        for key, value in config.items():
            if service_name == 'system':
                req = ServiceReq(key)
            elif isinstance(key, Type):
                req = CfgItemReq(service_name, key)
            elif service_name == 'marker_registry':
                req = MarkerReq(key)
            else:
                req = None
            if type(key) is not str:
                assert isinstance(key, Type)
                key = f'{key.module_name}-{key.name}'
            item_piece = ctl.item_piece(value)  # Expecting only MultiItemConfigCtl ctl instances.
            ctr = ctr_from_template_creg.animate(item_piece, service_name)
            module_name, var_name = project.reverse_resolve(item_piece)
            resource_tgt = target_set.factory.python_module_resource_by_module_name(module_name)
            assert isinstance(resource_tgt, ManualPythonModuleResourceTarget)
            _ = target_set.factory.config_items(service_name, key, req, provider=resource_tgt, ctr=ctr)


def create_python_modules(rc_config, root_dir, cache, cached_count, target_set, prefix, path_to_text, target_project, all_imports_known_tgt):
    import_target_list = []
    for path, text in path_to_text.items():
        ext = '.dyn.py'
        if not path.endswith(ext):
            continue
        stem = path[:-len(ext)]
        parts = stem.split('/')
        name = parts[-1]
        full_name = prefix + '.' + stem.replace('/', '.')
        dir = '/'.join(parts[:-1])
        resource_path = root_dir.joinpath(dir, f'{name}.resources.yaml').relative_to(hyperapp_dir)
        target_set.add_module_name(full_name, name)
        src = PythonModuleSrc(full_name, name, str(root_dir / path), resource_path, text)
        try:
            resource_text = hyperapp_dir.joinpath(resource_path).read_text()
        except FileNotFoundError:
            pass
        else:
            if not resource_text.startswith(AUTO_GEN_LINE):
                resource_dir = root_dir / dir
                resource_tgt = ManualPythonModuleResourceTarget(
                    target_set, src, target_project, resource_dir, resource_text)
                target_set.add(resource_tgt)
                continue
        import_tgt = ImportTarget(rc_config, cache, cached_count, target_set, target_project, target_project.types, all_imports_known_tgt, src)
        target_set.add(import_tgt)
        import_target_list.append(import_tgt)
    return import_target_list


def create_target_set(
        config_ctl, ctr_from_template_creg, rc_config,
        root_dir, cache, cached_count, globals_targets, target_project, path_to_text, imports):
    target_set = TargetSet(globals_targets, root_dir, target_project.types, imports)
    all_imports_known_tgt = AllImportsKnownTarget()
    target_set.add(all_imports_known_tgt)
    path = root_dir.joinpath('config.resources.yaml').relative_to(hyperapp_dir)
    config_tgt = ConfigResourceTarget(target_project, resource_dir=root_dir, module_name='config', path=path)
    target_set.add(config_tgt)
    import_target_list = create_python_modules(
        rc_config, root_dir, cache, cached_count, target_set, target_project.name, path_to_text, target_project, all_imports_known_tgt)
    for import_tgt in import_target_list:
        import_tgt.create_job_target()
    return target_set
