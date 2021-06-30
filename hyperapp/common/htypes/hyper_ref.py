from .htypes import tString, tBinary, tDateTime, TList
from .record import TRecord, ref_t


capsule_t = TRecord('capsule', {
    'type_ref': ref_t,
    'encoding': tString,  # used for both encoded_object and making ref to this capsule
    'encoded_object': tBinary,
    })

bundle_t = TRecord('bundle', {
    'roots': TList(ref_t),
    'aux_roots': TList(ref_t),
    'capsule_list': TList(capsule_t),
    })
