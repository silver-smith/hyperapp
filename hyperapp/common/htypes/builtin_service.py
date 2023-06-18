from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    tString,
    )


builtin_service_t = TRecord(BUILTIN_MODULE_NAME, 'legacy_service', {
    'name': tString,
    })
