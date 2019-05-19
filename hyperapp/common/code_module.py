from collections import OrderedDict

from .htypes import (
    tString,
    TRecord,
    TList,
    ref_t,
    builtin_type_names,
    )


type_import_t = TRecord('type_import', OrderedDict([
    ('type_module_name', tString),
    ('type_name', tString),
    ('type_ref', ref_t),
    ]))

code_import_t = TRecord('code_import', OrderedDict([
    ('import_name', tString),
    ('code_module_ref', ref_t),
    ]))

code_module_t = TRecord('code_module', OrderedDict([
    ('module_name', tString),
    ('type_import_list', TList(type_import_t)),
    ('code_import_list', TList(code_import_t)),
    ('source', tString),
    ('file_path', tString),
    ]))

builtin_module_t = TRecord('builtin_module', OrderedDict([
    ('module_name', tString),  # full dotted name
    ]))


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
    builtin_module_t,
    ]


def register_code_module_types(ref_registry, type_resolver):
    for t in _code_module_type_list:
        type_resolver.register_builtin_type(ref_registry, t)
    builtin_type_names.update(t.name for t in _code_module_type_list)
