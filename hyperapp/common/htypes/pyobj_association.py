from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    tString,
    ref_t,
    )


python_object_association_t = TRecord(BUILTIN_MODULE_NAME, 'python_object_association', {
    't': ref_t,
    'function': ref_t,
    })


python_object_association_def_t = TRecord(BUILTIN_MODULE_NAME, 'python_object_association_def', {
    't': tString,
    'function': tString,
    })
