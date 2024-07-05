import importlib
import importlib.util
import logging
import sys

from hyperapp.common.htypes import HException

log = logging.getLogger(__name__)


ROOT_PACKAGE = 'hyperapp.dynamic'


class PythonModuleImportError(Exception):

    def __init__(self, message, original_error, import_name):
        super().__init__(message)
        self.original_error = original_error
        self.import_name = import_name


def is_sub_path(sub_path, full_path):
    for x, y in zip(
        sub_path.split('.'),
        full_path.split('.'),
        ):
        if x != y:
            return False
    return True


class Finder:

    _is_package = False

    def create_module(self, spec):
        return None  # Use default semantics.

    def get_spec(self, fullname):
        return importlib.util.spec_from_loader(fullname, self, is_package=self._is_package)

    def exec_module(self, module):
        pass

    
class _EmptyLoader(Finder):
    _is_package = True


class _MetaPathFinder:

    def __init__(self, module_name_to_loader, sub_path_loaders):
        # These are modified after this constructor is called.
        self._module_name_to_loader = module_name_to_loader
        self._sub_path_loaders = sub_path_loaders  # 'some.module.' -> loader

    # MetaPathFinder implementation.
    def find_spec(self, fullname, path, target=None):
        log.debug('find_spec fullname=%r path=%r target=%r', fullname, path, target)
        loader = self._module_name_to_loader.get(fullname)
        if loader:
            return loader.get_spec(fullname)
        for prefix, loader in self._sub_path_loaders.items():
            if fullname.startswith(prefix) and is_sub_path(prefix, fullname):
                spec = loader.get_spec(fullname)
                if spec is not None:
                    return spec


class PythonImporter:

    def __init__(self):
        self._module_name_to_loader = {ROOT_PACKAGE: _EmptyLoader()}
        self._sub_path_loaders = {}
        self._meta_path_finder = _MetaPathFinder(self._module_name_to_loader, self._sub_path_loaders)
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
        sub_path_loaders = {}
        module_name_to_loader = {module_name: root_loader}
        for sub_name, loader in sub_loader_dict.items():
            full_name = f'{module_name}.{sub_name}'
            if full_name.endswith('.*'):
                # This is auto-importer; it wants full_name.
                loader.set_base_module_name(module_name)
                sub_path_loaders[full_name[:-2]] = loader
            else:
                module_name_to_loader[full_name] = loader
        # Should reload if already loaded (pytest case).
        for full_name in module_name_to_loader:
            try:
                del sys.modules[full_name]
            except KeyError:
                pass
        self._sub_path_loaders.update(sub_path_loaders)
        self._module_name_to_loader.update(module_name_to_loader)
        log.debug('Import python module: %s', module_name)
        try:
            module = importlib.import_module(module_name)
        except HException:
            raise
        except Exception as x:
            raise PythonModuleImportError(str(x), x, module_name) from x
        self._imported_modules += module_name_to_loader
        return module
