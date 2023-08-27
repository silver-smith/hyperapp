from hyperapp.common.python_importer import Finder

from .services import (
    pyobj_creg,
    )


class RecorderObject:

    def __init__(self, prefix, resources, packages, imported_set):
        self._prefix = prefix
        self._resources = resources
        self._packages = packages
        self._imported_set = imported_set

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        resource_path = (*self._prefix, name)
        resource_path_str = '.'.join(resource_path)
        if resource_path in self._packages:
            return RecorderObject(resource_path, self._resources, self._packages, self._imported_set)
        try:
            resource_ref = self._resources[resource_path]
        except KeyError:
            if len(self._prefix) >= 2 and self._prefix[0] == 'code':
                return self._load_code_module_attr(name)
            # Use AttributeError to give other importers a chance.
            raise AttributeError(name)
        object = self._load_resource(resource_path_str, resource_ref)
        self._imported_set.add(resource_path)
        return object

    def _load_code_module_attr(self, attr_name):
        module_path = self._prefix
        module_path_str = '.'.join(module_path)
        try:
            code_module_ref = self._resources[module_path]
        except KeyError:
            msg = f"Attempt to get attribute {attr_name!r} from unknown code module: {module_path_str}"
            raise RuntimeError(msg)
        module = self._load_resource(module_path_str, code_module_ref)
        self._imported_set.add(module_path)
        if not hasattr(module, attr_name):
            msg = f"Attempt to import missing attribute {attr_name!r} from code module: {module_path_str}"
            raise RuntimeError(msg)
        return getattr(module, attr_name)

    def _load_resource(self, resource_path_str, resource_ref):
        try:
            return pyobj_creg.invite(resource_ref)
        except Exception as x:
            raise RuntimeError(f"Error importing {resource_path_str!r}: {x}")


class ImportRecorder(Finder):

    _is_package = True

    def __init__(self, piece):
        self._base_module_name = None
        self._resources = {
            r.name: r.resource
            for r in piece.resources
            }
        self._packages = set()
        for name in self._resources.keys():
            for i in range(1, len(name)):
                prefix = name[:i]
                if prefix not in self._resources:
                    self._packages.add(prefix)
        self._imported_set = set()

    def reset(self):
        self._imported_set.clear()

    def used_imports(self):
        return list(sorted(self._imported_set))

    def set_base_module_name(self, name):
        self._base_module_name = name

    def _name_prefix(self, fullname):
        assert fullname.startswith(self._base_module_name + '.')
        rel_name = fullname[len(self._base_module_name) + 1 :]
        return tuple(rel_name.split('.'))

    # Finder interface:

    def get_spec(self, fullname):
        prefix = tuple(self._name_prefix(fullname))
        if prefix in self._packages or prefix in self._resources:
            return super().get_spec(fullname)
        else:
            return None

    def create_module(self, spec):
        prefix = self._name_prefix(spec.name)
        return RecorderObject(prefix, self._resources, self._packages, self._imported_set)

    def exec_module(self, module):
        pass
