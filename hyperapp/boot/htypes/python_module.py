from . import (
    BUILTIN_MODULE_NAME,
    TList,
    TRecord,
    tString,
    ref_t,
    )


import_rec_t = TRecord(BUILTIN_MODULE_NAME, 'import_rec', {
    'full_name': tString,
    'resource': ref_t,
    })

python_module_t = TRecord(BUILTIN_MODULE_NAME, 'python_module', {
    'module_name': tString,
    'source': tString,
    'file_path': tString,
    'import_list': TList(import_rec_t),
    })

import_rec_def_t = TRecord(BUILTIN_MODULE_NAME, 'import_rec_def', {
    'full_name': tString,
    'resource': tString,
    })

python_module_def_t = TRecord(BUILTIN_MODULE_NAME, 'python_module_def', {
    'module_name': tString,
    'file_name': tString,
    'import_list': TList(import_rec_def_t),
    })
