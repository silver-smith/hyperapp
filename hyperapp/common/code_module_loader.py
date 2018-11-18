import yaml
from .code_module import type_import_t, code_import_t, code_module_t


class CodeModuleLoader(object):

    def __init__(self, ref_registry, local_type_module_registry, local_code_module_registry):
        self._ref_registry = ref_registry
        self._local_type_module_registry = local_type_module_registry
        self._local_code_module_registry = local_code_module_registry

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
                type_ref = local_type_module.get(type_name)
                assert type_ref, "%s: Unknown type: %s.%s" % (info_path, type_module_name, type_name)
                type_import_list.append(type_import_t(type_module_name, type_name, type_ref))
        code_import_list = []
        for import_module_name in info['import'].get('code', []):
            assert isinstance(import_module_name, str), (
                '%s: string list is expected at import/code, but got: %r', file_path, import_module_name)
            import_module_ref = self._local_code_module_registry[import_module_name]
            code_import_list.append(code_import_t(import_module_name, import_module_ref))
        code_module = code_module_t(module_name, type_import_list, [], source, str(source_path))
        code_module_ref = self._ref_registry.register_object(code_module)
        self._local_code_module_registry.register(module_name, code_module_ref)
        return code_module
