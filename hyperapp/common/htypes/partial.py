from . import (
    BUILTIN_MODULE_NAME,
    TList,
    TRecord,
    ref_t,
    tString,
    )


partial_param_t = TRecord(BUILTIN_MODULE_NAME, 'partial_param', {
    'name': tString,
    'value': ref_t,
    })

partial_param_def_t = TRecord(BUILTIN_MODULE_NAME, 'partial_param_def', {
    'name': tString,
    'value': tString,
    })


partial_t = TRecord(BUILTIN_MODULE_NAME, 'partial', {
    'function': ref_t,
    'params': TList(partial_param_t),
    })

partial_def_t = TRecord(BUILTIN_MODULE_NAME, 'partial_def', {
    'function': tString,
    'params': TList(partial_param_def_t),
    })
