import importlib
import importlib.util
import logging
import sys

log = logging.getLogger(__name__)


ROOT_PACKAGE = 'hyperapp.dynamic'


class Finder:

    _is_package = False

    def create_module(self, spec):
        return None  # Use default semantics.

    def get_spec(self, fullname):
        return importlib.util.spec_from_loader(fullname, self, is_package=self._is_package)

    
class _EmptyLoader(Finder):

    _is_package = True

    def exec_module(self, module):
        pass


class _MetaPathFinder:

    def __init__(self, module_name_to_loader):
        self._module_name_to_loader = module_name_to_loader

    # MetaPathFinder implementation.
    def find_spec(self, fullname, path, target=None):
        log.debug('find_spec fullname=%r path=%r target=%r', fullname, path, target)
        loader = self._module_name_to_loader.get(fullname)
        if loader:
            return loader.get_spec(fullname)


class PythonImporter:

    def __init__(self):
        self._module_name_to_loader = {ROOT_PACKAGE: _EmptyLoader()}
        self._meta_path_finder = _MetaPathFinder(self._module_name_to_loader)
        self._imported_modules = []

    def register_meta_hook(self):
        sys.meta_path.append(self._meta_path_finder)

    def unregister_meta_hook(self):
        sys.meta_path.remove(self._meta_path_finder)

    def module_imported(self, module_name):
        return module_name in sys.modules

    def remove_modules(self):
        for module_name in self._imported_modules:
            try:
                del sys.modules[module_name]
            except KeyError:
                pass  # It may be added to loader, but never actually imported by anyone.

    def import_module(self, module_name, root_loader, sub_loader_dict):
        module_name_to_loader = {module_name: root_loader}
        for sub_name, loader in sub_loader_dict.items():
            full_name = f'{module_name}.{sub_name}'
            module_name_to_loader[full_name] = loader
        # Should reload if already loaded (pytest case).
        for full_name in module_name_to_loader:
            try:
                del sys.modules[full_name]
            except KeyError:
                pass
        self._module_name_to_loader.update(module_name_to_loader)
        log.debug('Import python module: %s', module_name)
        module = importlib.import_module(module_name)
        self._imported_modules += module_name_to_loader
        return module
