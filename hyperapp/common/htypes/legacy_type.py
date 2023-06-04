from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    ref_t,
    )


legacy_type_t = TRecord(BUILTIN_MODULE_NAME, 'legacy_type', {
    'type_ref': ref_t,
    })

