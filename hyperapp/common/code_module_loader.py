import logging
from collections import defaultdict, namedtuple

import yaml

from .code_module import type_import_t, code_import_t, code_module_t

log = logging.getLogger(__name__)

_ModuleInfo = namedtuple('_ModuleInfo', 'info_path source_path type_import_dict code_import_list provide require')


class Registry:

    def __init__(self):
        self.by_name = {}  # str -> code_module_t
        self.by_requirement = defaultdict(set)  # str -> code_module_t set
        self.module_provides = defaultdict(set)  # module name -> provide set


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
        ext = '.dyn.py'
        name_to_info = {}
        for source_path in root_dir.rglob(f'*{ext}'):
            if 'test' in source_path.relative_to(root_dir).parts:
                continue  # Skip test subdirectories.
            info_path = source_path.parent.joinpath(source_path.name[:-len(ext)] + '.yaml')
            rpath = str(source_path.relative_to(root_dir))
            module_name = rpath[:-len(ext)].replace('/', '.')
            if not info_path.exists():
                log.warning("No info path for dynamic module exists, skipping: %s", info_path)
                continue
            raw_info = yaml.safe_load(info_path.read_text()) or {}
            imports = raw_info.get('import', {})
            info = _ModuleInfo(
                info_path=info_path,
                source_path=source_path,
                type_import_dict=imports.get('types', {}),
                code_import_list=imports.get('code', []),
                provide=raw_info.get('provide', []),
                require=raw_info.get('require', []),
                )
            name_to_info[module_name] = info
            log.debug("Loaded code module info %r: %s", module_name, info)
        return name_to_info

    def _load_module(self, module_name, name_to_info, registry, dep_stack):
        if module_name in dep_stack:
            raise RuntimeError("Circular code module dependency: {}".format('->'.join([*dep_stack, module_name])))
        info = name_to_info[module_name]
        code_import_list = []
        for import_module_name in info.code_import_list:
            assert isinstance(import_module_name, str), (
                '%s: string list is expected at import/code, but got: %r', info.info_path, import_module_name)
            imported_module = registry.by_name.get(import_module_name)
            if not imported_module:
                if import_module_name not in name_to_info:
                    raise RuntimeError(f"Code module {module_name!r} wants unknown code module {import_module_name!r}.")
                imported_module = self._load_module(import_module_name, name_to_info, registry, [*dep_stack, module_name])
            imported_module_ref = self._mosaic.put(imported_module)
            code_import_list.append(code_import_t(import_module_name, imported_module_ref))
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
            type_import_list=tuple(type_import_list),
            code_import_list=tuple(code_import_list),
            provide=tuple(info.provide),
            require=tuple(info.require),
            source=source,
            file_path=str(info.source_path),
            )
        registry.by_name[module_name] = code_module
        for requirement in info.provide:
            registry.by_requirement[requirement].add(code_module)
            registry.module_provides[module_name].add(requirement)
        log.debug("Loaded code module %s", module_name)
        return code_module
