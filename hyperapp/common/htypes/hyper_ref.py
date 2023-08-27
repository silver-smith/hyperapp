from .htypes import BUILTIN_MODULE_NAME, tString, tBinary, TList
from .record import TRecord, ref_t


capsule_t = TRecord(BUILTIN_MODULE_NAME, 'capsule', {
    'type_ref': ref_t,
    'encoding': tString,  # used for both encoded_object and making ref to this capsule
    'encoded_object': tBinary,
    })

bundle_t = TRecord(BUILTIN_MODULE_NAME, 'bundle', {
    'roots': TList(ref_t),
    'associations': TList(ref_t),
    'capsule_list': TList(capsule_t),
    })
