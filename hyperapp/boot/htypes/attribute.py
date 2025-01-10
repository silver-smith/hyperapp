from . import (
    BUILTIN_MODULE_NAME,
    TRecord,
    ref_t,
    tString,
    )


attribute_t = TRecord(BUILTIN_MODULE_NAME, 'attribute', {
    'object': ref_t,
    'attr_name': tString,
    })

attribute_def_t = TRecord(BUILTIN_MODULE_NAME, 'attribute_def', {
    'object': tString,
    'attr_name': tString,
    })
