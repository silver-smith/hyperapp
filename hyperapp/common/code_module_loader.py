import yaml
from .htypes import type_import_t, code_module_t


class CodeModuleLoader(object):

    def __init__(self, local_type_module_registry):
        self._local_type_module_registry = local_type_module_registry

    def load_code_module(self, module_name, file_path):
        info_path = file_path.with_suffix('.yaml')
        source_path = file_path.with_suffix('.py')
        info = yaml.load(info_path.read_text())
        source = source_path.read_text()
        type_import_list = []
        for type_module_name, import_name_list in info['import']['types'].items():
            local_type_module = self._local_type_module_registry.resolve(type_module_name)
            assert local_type_module, "%s: Unknown type module: %s" % (info_path, type_module_name)
            for type_name in import_name_list:
                type_ref = local_type_module.resolve(type_name)
                assert type_ref, "%s: Unknown type: %s.%s" % (info_path, type_module_name, type_name)
                type_import_list.append(type_import_t(type_module_name, type_name, type_ref))
        return code_module_t(module_name, type_import_list, source, str(source_path))
