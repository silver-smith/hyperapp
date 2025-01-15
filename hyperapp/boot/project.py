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


class Project(ResourceRegistry):

    def __init__(self, builtin_types_dict, builtin_type_modules, builtin_service_resource_loader, type_module_loader, resource_module_factory, name):
        super().__init__()
        self._type_module_loader = type_module_loader
        self._resource_module_factory = resource_module_factory
        self._name = name
        self._types = {}  # Module name -> name -> mt piece.
        # TODO: Move following to separate project:
        self._types.update(builtin_types_dict)
        self.update_modules(builtin_type_modules)
        add_legacy_types_to_cache(self, builtin_type_modules)
        self.set_module('builtins', builtin_service_resource_loader(self))

    @property
    def types(self):
        return self._types

    def load(self, root_dir):
        path_to_text = load_texts(root_dir)
        self.load_types(root_dir, path_to_text)
        self.load_resources(root_dir, path_to_text)

    def load_types(self, root_dir, path_to_text):
        path_to_type_text = self._filter_by_ext(path_to_text, '.types')
        self._type_module_loader.load_texts(root_dir, path_to_type_text, self._types)
        legacy_type_modules = load_legacy_type_resources(self._types)
        self.update_modules(legacy_type_modules)
        add_legacy_types_to_cache(self, legacy_type_modules)

    def load_resources(self, root_dir, path_to_text):
        ext = '.resources.yaml'
        path_to_resource_text = self._filter_by_ext(path_to_text, ext)
        for path, text in path_to_resource_text.items():
            module_name = path[:-len(ext)].replace('/', '.')
            module = self._resource_module_factory(self, module_name, root_dir / path, text=text)
            self.set_module(module_name, module)

    def _filter_by_ext(self, path_to_text, ext):
        return {
            path: text for path, text
            in path_to_text.items()
            if path.endswith(ext)
            }
