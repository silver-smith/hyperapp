from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    ref_t,
    TypeNamespace,
    )


type_import_t = TRecord([
    Field('type_module_name', tString),
    Field('type_name', tString),
    Field('type_ref', ref_t),
    ], full_name=['code_module', 'type_import'])

code_module_t = TRecord([
    Field('module_name', tString),
    Field('type_import_list', TList(type_import_t)),
    Field('source', tString),
    Field('file_path', tString),
    ], full_name=['code_module', 'code_module'])


def make_code_module_namespace():
    namespace = TypeNamespace()
    for t in [
            code_module_t,
            ]:
        full_name = t.full_name
        module, name = full_name
        assert module == 'code_module'
        namespace[name] = t
    return namespace
