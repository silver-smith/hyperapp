from .htypes import tString, tBinary, TRecord, Field


hash_t = tBinary

ref_t = TRecord([
    Field('hash_algorithm', tString),
    Field('hash', hash_t),
    ], full_name=['builtins', 'ref'])
