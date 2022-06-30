from types import SimpleNamespace


class HyperTypesNamespace:

    def __init__(self, types, local_types):
        self._types = types
        self._local_types = local_types

    def __getattr__(self, name):
        if not name.startswith('_'):
            try:
                type_module = self._local_types[name]
            except KeyError:
                pass
            else:
                return self._type_module_namespace(type_module)
        raise RuntimeError(f"Unknown type module: {name!r}")

    def _type_module_namespace(self, type_module):
        name_to_type = {}
        for name, type_ref in type_module.items():
            name_to_type[name] = self._types.resolve(type_ref)
        return SimpleNamespace(**name_to_type)
