from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    TList,
    tString,
    ref_t,
    )


association_t = TRecord(BUILTIN_MODULE_NAME, 'association', {
    'bases': TList(ref_t),
    'key': TList(ref_t),
    'value': ref_t,
    })
