from .htypes import (
    BUILTIN_MODULE_NAME,
    tString,
    TRecord,
    TList,
    ref_t,
    )


type_import_t = TRecord(BUILTIN_MODULE_NAME, 'type_import', {
    'module_name': tString,
    'source_name': tString,
    'target_name': tString,
    })

type_def_t = TRecord(BUILTIN_MODULE_NAME, 'typedef', {
    'name': tString,
    'type': ref_t,
    })

type_module_t = TRecord(BUILTIN_MODULE_NAME, 'type_module', {
    'module_name': tString,
    'import_list': TList(type_import_t),
    'typedefs': TList(type_def_t),
    })
