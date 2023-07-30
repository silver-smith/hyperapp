from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    ref_t,
    tString,
    )


call_t = TRecord(BUILTIN_MODULE_NAME, 'call', {
    'function': ref_t,
    })

call_def_t = TRecord(BUILTIN_MODULE_NAME, 'call_def', {
    'function': tString,
    })
