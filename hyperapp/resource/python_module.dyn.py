import codecs
import inspect
import logging
import importlib
import yaml
from collections import defaultdict

from hyperapp.common.dict_decoders import NamedPairsDictDecoder
from hyperapp.common.dict_encoders import NamedPairsDictEncoder
from hyperapp.common.python_importer import ROOT_PACKAGE, Finder
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class PythonModuleResourceType:

    name = 'python_module'
    resource_t = htypes.python_module.python_module
    definition_t = htypes.python_module.python_module_def

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

    def resolve(self, definition, resolve_name, resource_path):
        import_list = tuple(
            htypes.python_module.import_rec(
                full_name=rec.full_name,
                resource=resolve_name(rec.resource),
                )
            for rec in definition.import_list
            )
        source_path = resource_path / definition.file_name
        return htypes.python_module.python_module(
            module_name=definition.module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
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


def sub_loader_dict(python_object_creg, import_list, root_module_name):
    loader_dict = {}
    module_dict = defaultdict(dict)
    for rec in import_list:
        resource = python_object_creg.invite(rec.resource)
        path = rec.full_name.split('.')
        if len(path) == 1:
            [module_name] = path
            if inspect.ismodule(resource):
                # This is code module import, resource is python module.
                module_dict[module_name] = resource.__dict__
            else:
                module_dict[module_name] = resource  # Auto-importer?
            continue
        for i in range(len(path)):
            package_name = '.'.join(path[:i])
            if package_name not in loader_dict:
                if package_name == 'htypes':
                    loader_dict[package_name] = _HTypeRootLoader()
                else:
                    loader_dict[package_name] = _PackageLoader()
            if path[0] == 'htypes' and i == 2:
                loader_dict['htypes'].sub_module_list.append(f'{root_module_name}.{package_name}')
        module_name = '.'.join(path[:-1])
        name = path[-1]
        module_dict[module_name][name] = resource
    loader_dict.update({
        name: _DictLoader(globals) if isinstance(globals, dict) else globals
        for name, globals in module_dict.items()
        })
    return loader_dict

                
def python_object(piece, mosaic, python_importer, python_object_creg):
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
            sub_loader_dict=sub_loader_dict(python_object_creg, piece.import_list, module_name))
    except Exception as x:
        raise RuntimeError(f"Error importing module {piece.module_name!r}: {x}")
            

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg[htypes.python_module.python_module] = PythonModuleResourceType()
        services.python_object_creg.register_actor(
            htypes.python_module.python_module, python_object,
            services.mosaic, services.python_importer, services.python_object_creg)
