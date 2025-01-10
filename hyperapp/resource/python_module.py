import codecs
import inspect
import logging
import importlib
import yaml
from collections import defaultdict
from pathlib import Path

from hyperapp.boot.htypes.python_module import import_rec_t, python_module_t, import_rec_def_t, python_module_def_t
from hyperapp.boot.htypes import HException
from hyperapp.boot.dict_decoder import NamedPairsDictDecoder
from hyperapp.boot.dict_encoder import NamedPairsDictEncoder
from hyperapp.boot.python_importer import ROOT_PACKAGE, PythonModuleImportError, Finder

log = logging.getLogger(__name__)


class PythonModuleResourceImportError(Exception):

    def __init__(self, message, original_error, import_name, module_name):
        super().__init__(message)
        self.original_error = original_error
        self.import_name = import_name
        self.module_name = module_name


class PythonModuleResourceType:

    name = 'python_module'
    resource_t = python_module_t
    definition_t = python_module_def_t

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<ResourceType: {self.name!r}>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_path):
        import_list = tuple(
            import_rec_t(
                full_name=rec.full_name,
                resource=resolver(rec.resource),
                )
            for rec in definition.import_list
            )
        source_path = resource_path / definition.file_name
        return python_module_t(
            module_name=definition.module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
            import_list=import_list,
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        import_list = tuple(
            import_rec_def_t(
                full_name=rec.full_name,
                resource=resolver(rec.resource),
                )
            for rec in resource.import_list
            )
        return python_module_def_t(
            module_name=resource.module_name,
            file_name=str(Path(resource.file_path).name),
            import_list=import_list,
            )


class _CodeModuleLoader(Finder):

    _is_package = True

    def __init__(self, name, source, file_path):
        self._name = name
        self._source = source
        self._file_path = file_path

    def exec_module(self, module):
        log.debug('Executing code module: %s', self._name)
        # Using compile allows associate file path with loaded module.
        ast = compile(self._source, self._file_path, 'exec')
        # Assign special globals here:
        # module.__dict__['__module_source__'] = self._code_module.source
        # module.__dict__['__module_ref__'] = self._code_module_ref
        module.__dict__['__file__'] = self._file_path
        exec(ast, module.__dict__)


class _DictLoader(Finder):

    def __init__(self, globals):
        self._globals = globals

    def exec_module(self, module):
        module.__dict__.update(self._globals)


class _SubCodeLoader(Finder):

    def __init__(self, module):
        self._module = module

    def create_module(self, spec):
        return self._module


class _PackageLoader(Finder):
    _is_package = True


# htypes.* modules are loaded automatically, without importing each of them manually.
class _HTypeRootLoader(Finder):

    _is_package = True

    def __init__(self):
        self.sub_module_list = []

    def exec_module(self, module):
        for module_name in self.sub_module_list:
            importlib.import_module(module_name)


def make_module_name(mosaic, module):
    module_ref = mosaic.put(module)
    hash_hex = codecs.encode(module_ref.hash[:10], 'hex').decode()
    return f'{ROOT_PACKAGE}.{module_ref.hash_algorithm}_{hash_hex}'


def sub_loader_dict(pyobj_creg, import_list, root_module_name):
    loader_dict = {}
    module_dict = defaultdict(dict)
    for rec in import_list:
        resource = pyobj_creg.invite(rec.resource)
        path = rec.full_name.split('.')
        prefix_len = len(path)
        if path[-1] == '*':
            prefix_len -= 1
        for i in range(1, prefix_len):
            package_name = '.'.join(path[:i])
            if package_name not in loader_dict:
                if package_name == 'htypes':
                    loader_dict[package_name] = _HTypeRootLoader()
                else:
                    loader_dict[package_name] = _PackageLoader()
            if path[0] == 'htypes' and i == 2:
                loader_dict['htypes'].sub_module_list.append(f'{root_module_name}.{package_name}')
        if path[-1] == '*':
            # An auto importer.
            module_name = rec.full_name
            module_dict[module_name] = resource
            continue
        if inspect.ismodule(resource):
            # This is code module import, resource is python module.
            module_dict[rec.full_name] = _SubCodeLoader(resource)
            continue
        module_name = '.'.join(path[:-1])
        name = path[-1]
        module_dict[module_name][name] = resource
    loader_dict.update({
        name: _DictLoader(globals) if isinstance(globals, dict) else globals
        for name, globals in module_dict.items()
        })
    return loader_dict

                
def python_module_pyobj(piece, mosaic, python_importer, pyobj_creg):
    module_name = make_module_name(mosaic, piece)
    if python_importer.module_imported(module_name):
        raise RuntimeError(f"Error: module {module_name} is aleady imported")
    root_loader = _CodeModuleLoader(
        name=piece.module_name,
        source=piece.source,
        file_path=piece.file_path,
        )
    try:
        return python_importer.import_module(
            module_name, root_loader,
            sub_loader_dict=sub_loader_dict(pyobj_creg, piece.import_list, module_name))
    except HException:
        raise
    except PythonModuleImportError as x:
        raise PythonModuleResourceImportError(str(x), x.original_error, x.import_name, piece.module_name) from x
