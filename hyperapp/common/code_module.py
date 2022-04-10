from .htypes import (
    BUILTIN_MODULE_NAME,
    tString,
    TRecord,
    TList,
    ref_t,
    )


type_import_t = TRecord(BUILTIN_MODULE_NAME, 'type_import', {
    'type_module_name': tString,
    'type_name': tString,
    'type_ref': ref_t,
    })

code_import_t = TRecord(BUILTIN_MODULE_NAME, 'code_import', {
    'import_name': tString,
    'code_module_ref': ref_t,
    })

code_module_t = TRecord(BUILTIN_MODULE_NAME, 'code_module', {
    'module_name': tString,
    'type_import_list': TList(type_import_t),
    'code_import_list': TList(code_import_t),
    'provide': TList(tString),
    'require': TList(tString),
    'source': tString,
    'file_path': tString,
    })

builtin_module_t = TRecord(BUILTIN_MODULE_NAME, 'builtin_module', {
    'module_name': tString,  # full dotted name
    })


_code_module_type_list = [
    code_module_t,
    builtin_module_t,
    ]


def register_code_module_types(builtin_types, mosaic, types):
    for t in _code_module_type_list:
        builtin_types.register(mosaic, types, t)
