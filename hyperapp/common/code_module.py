from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    ref_t,
    TypeNamespace,
    builtin_type_names,
    )


type_import_t = TRecord([
    Field('type_module_name', tString),
    Field('type_name', tString),
    Field('type_ref', ref_t),
    ], name='type_import')

code_import_t = TRecord([
    Field('import_name', tString),
    Field('code_module_ref', ref_t),
    ], name='code_import')

code_module_t = TRecord([
    Field('module_name', tString),
    Field('type_import_list', TList(type_import_t)),
    Field('code_import_list', TList(code_import_t)),
    Field('source', tString),
    Field('file_path', tString),
    ], name='code_module')


class LocalCodeModuleRegistry(object):

    def __init__(self):
        self._registry = {}  # module name -> ref_t

    def register(self, code_module_name, code_module_ref):
        assert isinstance(code_module_ref, ref_t), repr(code_module_ref)
        self._registry[code_module_name] = code_module_ref

    def resolve(self, name):
        return self._registry.get(name)

    def __getitem__(self, name):
        return self._registry[name]


_code_module_type_list = [
    code_module_t,
    ]


def register_code_module_types(ref_registry, type_resolver):
    for t in _code_module_type_list:
        type_resolver.register_builtin_type(ref_registry, t)
    builtin_type_names.update(t.name for t in _code_module_type_list)
