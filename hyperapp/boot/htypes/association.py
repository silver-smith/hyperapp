from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    TList,
    tString,
    ref_t,
    )


association_t = TRecord(BUILTIN_MODULE_NAME, 'association', {
    'bases': TList(ref_t),
    'service_name': tString,
    'cfg_item': ref_t,
    })
