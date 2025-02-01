import logging
from collections import namedtuple

import yaml

from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache, load_legacy_type_resources
from hyperapp.boot.resource.resource_registry import ResourceRegistry

log = logging.getLogger(__name__)

RESOURCE_EXT = '.resources.yaml'

ProjectRec = namedtuple('ProjectRec', 'name imports')


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


def _config_project_name(path):
    name = path.split('/')[-1]
    if not name.endswith(RESOURCE_EXT):
        return None
    stem = path[:-len(RESOURCE_EXT)]
    parts = stem.split('.')
    if len(parts) > 1 and parts[-1] == 'config':
        dir = '.'.join(path.split('/')[:-1])
        if dir:
            return f'{dir}.{stem}'
        else:
            return stem
    return None
            

def separate_configs(path_to_text):
    project_path_to_text = {}
    config_path_to_text = {}
    for path, text in path_to_text.items():
        if _config_project_name(path):
            config_path_to_text[path] = text
        else:
            project_path_to_text[path] = text
    return (project_path_to_text, config_path_to_text)


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

    def __init__(self, builtins_project, type_module_loader, resource_module_factory, path, name, imports=None):
        project_imports = imports or set()
        all_imports = {builtins_project, *project_imports}
        super().__init__(all_imports)
        self._type_module_loader = type_module_loader
        self._resource_module_factory = resource_module_factory
        self._project_imports = project_imports
        self._path = path
        self._name = name
        self._types = {}  # Module name -> name -> mt piece.

    def __repr__(self):
        return f"<Project {self._name!r}>"

    @property
    def name(self):
        return self._name

    # Root directory or resource path.
    @property
    def path(self):
        return self._path

    @property
    def imports(self):
        return self._project_imports

    @property
    def types(self):
        return self._types

    def load(self, path_to_text):
        log.debug("Project %s: loading %d files", self._name, len(path_to_text))
        self.load_types(path_to_text)
        self.load_resources(path_to_text)

    def load_types(self, path_to_text):
        for project in self._imports:
            self._types.update(project.types)
        path_to_type_text = self._filter_by_ext(path_to_text, '.types')
        self._type_module_loader.load_texts(path_to_type_text, self._types)
        legacy_type_modules = load_legacy_type_resources(self._types)
        self.update_modules(legacy_type_modules)
        add_legacy_types_to_cache(self, legacy_type_modules)

    def load_resources(self, path_to_text):
        path_to_resource_text = self._filter_by_ext(path_to_text, RESOURCE_EXT)
        for path, text in path_to_resource_text.items():
            if self._path.is_dir():
                stem = path[:-len(RESOURCE_EXT)].replace('/', '.')
                module_name = self._name + '.' + stem
                module_path = self._path / path
            else:
                module_name = self._name
                module_path = self._path.parent / path
            module = self._resource_module_factory(self, module_name, module_path, text=text)
            self.set_module(module_name, module)

    def _filter_by_ext(self, path_to_text, ext):
        return {
            path: text for path, text
            in path_to_text.items()
            if path.endswith(ext)
            }


def load_projects_file(path):
    config = yaml.safe_load(path.read_text())
    name_to_rec = {}
    for name, info in config.items():
        if info:
            imports = info.get('imports', [])
        else:
            imports = []
        name_to_rec[name] = ProjectRec(name, imports)
    return name_to_rec


def load_projects_from_file(project_factory, path, filter):
    name_to_rec = load_projects_file(path)
    root_dir = path.parent
    name_to_project = {}
    for rec in name_to_rec.values():
        if rec.name not in filter:
            continue
        imports = {
            name_to_project[import_name]
            for import_name in rec.imports
            }
        project_dir = root_dir / rec.name
        path_to_text = load_texts(project_dir)
        project_path_to_text, config_path_to_text = separate_configs(path_to_text)
        project = project_factory(project_dir, rec.name, imports)
        project.load(project_path_to_text)
        name_to_project[rec.name] = project
        for path, text in config_path_to_text.items():
            config_name = _config_project_name(path)
            project_name = f'{rec.name}.{config_name}'
            config_project = project_factory(project_dir / path, project_name, imports={project})
            config_project.load({path: text})
            name_to_project[project_name] = config_project
            
    return name_to_project
