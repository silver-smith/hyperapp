from functools import partial

from hyperapp.common.module import Module


class UnknownResourceName(Exception):
    pass


class ResourceRegistry:

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._name_pair_to_ref = {}
        self._ref_to_name_pair = {}
        self._module_reg = {}

    def __getitem__(self, name_pair):
        return self.resolve(name_pair)

    def set_module(self, name, module):
        self._module_reg[name] = module

    def update_modules(self, module_dict):
        self._module_reg.update(module_dict)

    def check_has_name(self, name_pair):
        if name_pair in self._name_pair_to_ref:
            return
        module_name, var_name = name_pair
        try:
            module = self._module_reg[module_name]
        except KeyError:
            raise UnknownResourceName(f"Unknown module: {module_name!r}")
        if var_name not in module:
            raise UnknownResourceName(f"Module {module_name} does not have {var_name!r}")

    def resolve(self, name_pair):
        try:
            return self._name_pair_to_ref[name_pair]
        except KeyError:
            pass
        module_name, var_name = name_pair
        try:
            module = self._module_reg[module_name]
        except KeyError:
            raise RuntimeError(f"Error resolving {module_name}:{var_name}: Unknown module {module_name!r}")
        piece = module[var_name]
        piece_ref = self._mosaic.put(piece)
        self._name_pair_to_ref[name_pair] = piece_ref
        self._ref_to_name_pair[piece_ref] = name_pair
        return piece_ref

    def reverse_resolve(self, piece_ref):
        try:
            return self._ref_to_name_pair[piece_ref]
        except KeyError:
            raise RuntimeError(f"Not are known resource: {piece!r}")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_registry_factory = partial(ResourceRegistry, services.mosaic)
        services.resource_registry = services.resource_registry_factory()
