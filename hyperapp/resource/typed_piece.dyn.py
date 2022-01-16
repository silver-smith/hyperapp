from functools import partial

from hyperapp.common.module import Module


def factory(local_type_module_registry, types, data, resolve_name):
    module_name, type_name = data['piece_t'].split('.')
    type_module = local_type_module_registry[module_name]
    type_ref = type_module[type_name]
    t = types.resolve(type_ref)
    return t()  # Only types with no fields are supported.


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['typed_piece'] = partial(
            factory, services.type_module_loader.registry, services.types)
