from .htypes import tString, tBinary, TRecord, Field, TList


hash_t = tBinary

ref_t = TRecord([
    Field('hash_algorithm', tString),
    Field('hash', hash_t),
    ], name='ref')

capsule_t = TRecord([
    Field('type_ref', ref_t),
    Field('encoding', tString),  # used for both encoded_object and making ref to this capsule
    Field('encoded_object', tBinary),
    ], name='capsule')

route_t = TRecord([
    Field('endpoint_ref', ref_t),
    Field('transport_ref', ref_t),
    ], name='route')

bundle_t = TRecord([
    Field('roots', TList(ref_t)),
    Field('capsule_list', TList(capsule_t)),
    Field('route_list', TList(route_t)),
    ], name='bundle')


resource_path_t = TList(tString, name='resource_path')

resource_key_t = TRecord([
    Field('module_ref', ref_t),
    Field('path', resource_path_t),
    ], name='resource_key')
