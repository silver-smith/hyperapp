from functools import partial

from hyperapp.common.module import Module


class UnknownResourceName(Exception):
    pass


class ResourceRegistry:

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._name_pair_to_piece = {}
        self._piece_to_name_pair = {}
        self._module_registry = {}

    def __getitem__(self, name_pair):
        return self.resolve(name_pair)

    # def __iter__(self):
    #     for module_name, module in self._module_registry.items():
    #         for var_name in module:
    #             yield (module_name, var_name)

    @property
    def associations(self):
        association_set = set()
        for module in self._module_registry.values():
            association_set |= module.associations
        return association_set

    def set_module(self, name, module):
        self._module_registry[name] = module

    def remove_module(self, name):
        del self._module_registry[name]
        self._piece_to_name_pair.clear()
        self._name_pair_to_piece.clear()

    def update_modules(self, module_dict):
        self._module_registry.update(module_dict)

    def add_to_cache(self, name_pair, piece):
        self._name_pair_to_piece[name_pair] = piece
        self._piece_to_name_pair[piece] = name_pair

    def check_has_name(self, name_pair):
        if name_pair in self._name_pair_to_piece:
            return
        module_name, var_name = name_pair
        try:
            module = self._module_registry[module_name]
        except KeyError:
            raise UnknownResourceName(f"Unknown module: {module_name!r}")
        if var_name not in module:
            raise UnknownResourceName(f"Module {module_name} does not have {var_name!r}")

    def resolve(self, name_pair):
        try:
            return self._name_pair_to_piece[name_pair]
        except KeyError:
            pass
        module_name, var_name = name_pair
        try:
            module = self._module_registry[module_name]
        except KeyError:
            raise RuntimeError(f"Error resolving {module_name}:{var_name}: Unknown module {module_name!r}")
        piece = module[var_name]
        self._name_pair_to_piece[name_pair] = piece
        self._piece_to_name_pair[piece] = name_pair
        return piece

    def reverse_resolve(self, piece):
        try:
            return self._piece_to_name_pair[piece]
        except KeyError:
            raise RuntimeError(f"Not a known resource: {piece!r}")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_registry_factory = partial(ResourceRegistry, services.mosaic)
        services.resource_registry = services.resource_registry_factory()
