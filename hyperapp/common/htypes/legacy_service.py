from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    tString,
    )


legacy_service_t = TRecord(BUILTIN_MODULE_NAME, 'legacy_service', {
    'name': tString,
    })
