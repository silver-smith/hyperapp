import yaml

from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache, load_legacy_type_resources
from hyperapp.boot.resource.resource_registry import ResourceRegistry


def load_texts(root_dir):
    path_to_text = {}
    for path in root_dir.rglob('*'):
        if path.is_dir():
            continue
        if path.suffix == '.pyc':
            continue
        rel_path = path.relative_to(root_dir)
        if 'test' in rel_path.parts:
            continue  # Skip pytest subdirectories.
        path_to_text[str(rel_path)] = path.read_text()
    return path_to_text



class BuiltinsProject(ResourceRegistry):

    def __init__(self, builtin_types_dict, builtin_type_modules, builtin_service_resource_loader):
        super().__init__()
        self._name = 'builtins'
        self._types = {}  # Module name -> name -> mt piece.
        self._types.update(builtin_types_dict)
        self.update_modules(builtin_type_modules)
        add_legacy_types_to_cache(self, builtin_type_modules)
        self.set_module('builtins', builtin_service_resource_loader(self))

    def __repr__(self):
        return f"<BuiltinsProject>"

    @property
    def name(self):
        return 'builtins'

    @property
    def types(self):
        return self._types


class Project(ResourceRegistry):

    def __init__(self, builtins_project, type_module_loader, resource_module_factory, dir, name, imports=None):
        project_imports = imports or set()
        all_imports = {builtins_project, *project_imports}
        super().__init__(all_imports)
        self._type_module_loader = type_module_loader
        self._resource_module_factory = resource_module_factory
        self._project_imports = project_imports
        self._dir = dir
        self._name = name
        self._types = {}  # Module name -> name -> mt piece.

    def __repr__(self):
        return f"<Project {self._name!r}>"

    @property
    def name(self):
        return self._name

    @property
    def dir(self):
        return self._dir

    @property
    def imports(self):
        return self._project_imports

    @property
    def types(self):
        return self._types

    def load(self):
        path_to_text = load_texts(self._dir)
        self.load_types(path_to_text)
        self.load_resources(path_to_text)

    def load_types(self, path_to_text):
        for project in self._imports:
            self._types.update(project.types)
        path_to_type_text = self._filter_by_ext(path_to_text, '.types')
        self._type_module_loader.load_texts(self._dir, path_to_type_text, self._types)
        legacy_type_modules = load_legacy_type_resources(self._types)
        self.update_modules(legacy_type_modules)
        add_legacy_types_to_cache(self, legacy_type_modules)

    def load_resources(self, path_to_text):
        ext = '.resources.yaml'
        path_to_resource_text = self._filter_by_ext(path_to_text, ext)
        for path, text in path_to_resource_text.items():
            stem = path[:-len(ext)].replace('/', '.')
            module_name = self._name + '.' + stem
            if 'config' in stem.split('.')[1:]:
                # Configs are loaded to separate projects as lcs layers.
                continue
            module = self._resource_module_factory(self, module_name, self._dir / path, text=text)
            self.set_module(module_name, module)

    def _filter_by_ext(self, path_to_text, ext):
        return {
            path: text for path, text
            in path_to_text.items()
            if path.endswith(ext)
            }


def load_projects_from_file(project_factory, path):
    config = yaml.safe_load(path.read_text())
    root_dir = path.parent
    name_to_project = {}
    for name, info in config.items():
        if info:
            imports = {
                name_to_project[import_name]
                for import_name in info.get('imports', [])
                }
        else:
            imports = set()
        project = project_factory(root_dir / name, name, imports)
        name_to_project[name] = project
    return name_to_project
