from .htypes import tString, tBinary, TRecord, Field, TList


hash_t = tBinary

ref_t = TRecord([
    Field('hash_algorithm', tString),
    Field('hash', hash_t),
    ], full_name=['builtins', 'ref'])

capsule_t = TRecord([
    Field('type_ref', ref_t),
    Field('encoding', tString),
    Field('encoded_object', tBinary),
    ], full_name=['builtins', 'capsule'])

route_t = TRecord([
    Field('endpoint_ref', ref_t),
    Field('transport_ref', ref_t),
    ], full_name=['builtins', 'route'])

bundle_t = TRecord([
    Field('roots', TList(ref_t)),
    Field('capsule_list', TList(capsule_t)),
    Field('route_list', TList(route_t)),
    ], full_name=['builtins', 'bundle'])
