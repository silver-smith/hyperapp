from collections import defaultdict, namedtuple

import yaml

from .code_module import type_import_t, code_import_t, code_module_t


DYN_MODULE_SUFFIX = '.dyn.py'


_ModuleInfo = namedtuple('_ModuleInfo', 'info_path source_path type_import_dict code_import_list provides requires')


class Registry:

    def __init__(self):
        self.by_name = {}
        self.by_requirement = defaultdict(set)


class CodeModuleLoader:

    def __init__(self, mosaic, local_type_module_registry):
        self._mosaic = mosaic
        self._local_type_module_registry = local_type_module_registry

    def load_code_modules(self, root_dir_list):
        name_to_info = {}
        for root_dir in root_dir_list:
            name_to_info.update(self._load_modules_info(root_dir))
        registry = Registry()
        for name in name_to_info:
            self._load_module(name, name_to_info, registry, [])
        return registry

    def _load_modules_info(self, root_dir):
        name_to_info = {}
        for info_path in root_dir.rglob('*.yaml'):
            if '.resources' in info_path.suffixes:
                continue  # Skip resources.
            if 'test' in info_path.relative_to(root_dir).parts:
                continue  # Skip test subdirectories.
            module_name = '.'.join(info_path.with_suffix('').relative_to(root_dir).parts)
            raw_info = yaml.safe_load(info_path.read_text()) or {}
            imports = raw_info.get('import', {})
            info = _ModuleInfo(
                info_path=info_path,
                source_path=info_path.with_suffix(DYN_MODULE_SUFFIX),
                type_import_dict=imports.get('types', {}),
                code_import_list=imports.get('code', []),
                provides=raw_info.get('provides', []),
                requires=raw_info.get('requires', []),
                )
            name_to_info[module_name] = info
        return name_to_info

    def _load_module(self, module_name, name_to_info, registry, dep_stack):
        if module_name in dep_stack:
            raise RuntimeError("Circular code module dependency: {}".format('->'.join([*dep_stack, module_name])))
        info = name_to_info[module_name]
        code_import_list = []
        for import_module_name in info.code_import_list:
            assert isinstance(import_module_name, str), (
                '%s: string list is expected at import/code, but got: %r', info.info_path, import_module_name)
            import_module_ref = registry.by_name.get(import_module_name)
            if not import_module_ref:
                if import_module_name not in name_to_info:
                    raise RuntimeError(f"Code module {module_name!r} wants unknown code module {import_module_name!r}.")
                import_module_ref = self._load_module(import_module_name, name_to_info, registry, [*dep_stack, module_name])
            code_import_list.append(code_import_t(import_module_name, import_module_ref))
        type_import_list = []
        for type_module_name, import_name_list in info.type_import_dict.items():
            try:
                local_type_module = self._local_type_module_registry[type_module_name]
            except KeyError:
                raise RuntimeError(f"{info.info_path}: Unknown type module: {type_module_name}")
            for type_name in import_name_list:
                try:
                    type_ref = local_type_module[type_name]
                except KeyError:
                    raise RuntimeError('Code module {0!r} wants type "{1}.{2}", but type module {1!r} does not have it'.format(
                        module_name, type_module_name, type_name))
                assert type_ref, "%s: Unknown type: %s.%s" % (info.info_path, type_module_name, type_name)
                type_import_list.append(type_import_t(type_module_name, type_name, type_ref))
        source = info.source_path.read_text()
        code_module = code_module_t(
            module_name=module_name,
            type_import_list=type_import_list,
            code_import_list=code_import_list,
            provides=info.provides,
            requires=info.requires,
            source=source,
            file_path=str(info.source_path),
            )
        code_module_ref = self._mosaic.put(code_module)
        registry.by_name[module_name] = code_module_ref
        for requirement in info.provides:
            registry.by_requirement[requirement].add(code_module_ref)
        return code_module_ref
