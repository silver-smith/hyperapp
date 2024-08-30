from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    ref_t,
    tString,
    )



raw_t = TRecord(BUILTIN_MODULE_NAME, 'raw', {
    'resource': ref_t,
    })

raw_def_t = TRecord(BUILTIN_MODULE_NAME, 'raw_def', {
    'resource': tString,
    })
