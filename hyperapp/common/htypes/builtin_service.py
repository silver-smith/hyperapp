from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    tString,
    )


builtin_service_t = TRecord(BUILTIN_MODULE_NAME, 'builtin_service', {
    'name': tString,
    })
