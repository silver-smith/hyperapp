from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    tString,
    ref_t,
    )


meta_association_t = TRecord(BUILTIN_MODULE_NAME, 'meta_association', {
    't': ref_t,
    'fn': ref_t,
    })

meta_association_def_t = TRecord(BUILTIN_MODULE_NAME, 'meta_association_def', {
    't': tString,
    'fn': tString,
    })
