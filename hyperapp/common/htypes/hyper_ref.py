from collections import OrderedDict
from .htypes import tString, tBinary, tDateTime, TList
from .record import TRecord


hash_t = tBinary

ref_t = TRecord('ref', OrderedDict([
    ('hash_algorithm', tString),
    ('hash', hash_t),
    ]))

capsule_t = TRecord('capsule', OrderedDict([
    ('type_ref', ref_t),
    ('encoding', tString),  # used for both encoded_object and making ref to this capsule
    ('encoded_object', tBinary),
    ]))

route_t = TRecord('route', OrderedDict([
    ('endpoint_ref', ref_t),
    ('transport_ref', ref_t),
    ('available_at', tDateTime),
    ]))

bundle_t = TRecord('bundle', OrderedDict([
    ('roots', TList(ref_t)),
    ('capsule_list', TList(capsule_t)),
    ('route_list', TList(route_t)),
    ]))


resource_path_t = TList(tString, name='resource_path')

resource_key_t = TRecord('resource_key', OrderedDict([
    ('base_ref', ref_t),
    ('path', resource_path_t),
    ]))
