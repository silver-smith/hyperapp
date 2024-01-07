from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    ref_t,
    )


code_registry_ctr_t = TRecord(BUILTIN_MODULE_NAME, 'code_registry_ctr', {
    'service': ref_t,
    'type': ref_t,
    })
