import codecs
import logging
import yaml

from hyperapp.common.python_importer import ROOT_PACKAGE, Finder
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def _collect_import_records(import_set, module_imports):
    def _collect(prefix, import_dict):
        for key, value in import_dict.items():
            if isinstance(value, str):
                yield '.'.join([*prefix, key]), value
            elif isinstance(value, dict):
                yield from _collect([*prefix, key], value)
            else:
                raise RuntimeError(f"String or dict expected at {key!r}: {value!r}")
    yield from _collect([], module_imports)


def load_python_module(module_name, path_stem, source_path):
    imports_path = path_stem.parent.joinpath(path_stem.name + '.imports.yaml')
    import_dict = yaml.safe_load(imports_path.read_text())
    import_set = set(import_dict['import'])
    module = htypes.python_module.python_module(
        module_name=module_name,
        source=source_path.read_text(),
        file_path=str(source_path),
        import_list=tuple(_collect_import_records(import_set, import_dict['module_imports'])),
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
        exec(ast, module.__dict__)


def make_module_name(mosaic, module):
    module_ref = mosaic.put(module)
    hash_hex = codecs.encode(module_ref.hash[:10], 'hex').decode()
    return f'{ROOT_PACKAGE}.{module_ref.hash_algorithm}_{hash_hex}'


def python_object(piece, mosaic, python_importer, python_object_creg):
    module_name = make_module_name(mosaic, piece)
    assert not python_importer.module_imported(module_name)
    root_loader = _CodeModuleLoader(
        name=piece.module_name,
        source=piece.source,
        file_path=piece.file_path,
        )
    return python_importer.import_module(module_name, root_loader, sub_loader_dict={})
            

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_creg.register_actor(
            htypes.python_module.python_module, python_object,
            services.mosaic, services.python_importer, services.python_object_creg)
