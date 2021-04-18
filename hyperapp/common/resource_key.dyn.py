import sys

from hyperapp.common.htypes import phony_ref, resource_key_t


def module_resource_key(module_name, path=()):
    module = sys.modules[module_name]
    module_ref = module.__dict__.get('__module_ref__') or phony_ref(module_name.split('.')[-1])
    return resource_key_t(module_ref, tuple(path))
