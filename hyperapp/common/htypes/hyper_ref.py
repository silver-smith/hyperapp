from .htypes import tString, tBinary, TRecord, Field, TList


hash_t = tBinary

ref_t = TRecord('ref', [
    Field('hash_algorithm', tString),
    Field('hash', hash_t),
    ])

capsule_t = TRecord('capsule', [
    Field('type_ref', ref_t),
    Field('encoding', tString),  # used for both encoded_object and making ref to this capsule
    Field('encoded_object', tBinary),
    ])

route_t = TRecord('route', [
    Field('endpoint_ref', ref_t),
    Field('transport_ref', ref_t),
    ])

bundle_t = TRecord('bundle', [
    Field('roots', TList(ref_t)),
    Field('capsule_list', TList(capsule_t)),
    Field('route_list', TList(route_t)),
    ])


resource_path_t = TList(tString, name='resource_path')

resource_key_t = TRecord('resource_key', [
    Field('module_ref', ref_t),
    Field('path', resource_path_t),
    ])
