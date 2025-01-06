
class UnknownResourceName(Exception):
    pass


class ResourceRegistry:

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._name_pair_to_piece = {}
        self._piece_to_name_pair = {}
        self._module_registry = {}

    def clone(self):
        registry = ResourceRegistry(self._mosaic)
        registry._name_pair_to_piece.update(self._name_pair_to_piece)
        registry._piece_to_name_pair.update(self._piece_to_name_pair)
        registry._module_registry.update(self._module_registry)
        return registry

    def __getitem__(self, name_pair):
        return self.resolve(name_pair)

    def __contains__(self, name_pair):
        if name_pair in self._name_pair_to_piece:
            return True
        module_name, var_name = name_pair
        try:
            module = self._module_registry[module_name]
        except KeyError:
            raise RuntimeError(f"Error resolving {module_name}:{var_name}: Unknown module {module_name!r}")
        return var_name in module

    # def __iter__(self):
    #     for module_name, module in self._module_registry.items():
    #         for var_name in module:
    #             yield (module_name, var_name)

    @property
    def module_list(self):
        return list(self._module_registry)

    def get_module(self, module_name):
        return self._module_registry.get(module_name)

    def set_module(self, name, module):
        self._module_registry[name] = module

    def remove_module(self, name):
        del self._module_registry[name]
        for name_pair, piece in list(self._name_pair_to_piece.items()):
            module_name, var_name = name_pair
            if module_name == name:
                del self._piece_to_name_pair[piece]
                del self._name_pair_to_piece[name_pair]

    def update_modules(self, module_dict):
        self._module_registry.update(module_dict)

    def add_to_cache(self, name_pair, piece):
        self._name_pair_to_piece[name_pair] = piece
        self._piece_to_name_pair[piece] = name_pair

    def remove_from_cache(self, name_pair):
        try:
            piece = self._name_pair_to_piece[name_pair]
        except KeyError:
            return
        del self._name_pair_to_piece[name_pair]
        del self._piece_to_name_pair[piece]

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
        piece = module[var_name]  # KeyError propagates here.
        self._name_pair_to_piece[name_pair] = piece
        self._piece_to_name_pair[piece] = name_pair
        return piece

    def has_piece(self, piece):
        return piece in self._piece_to_name_pair

    def reverse_resolve(self, piece):
        try:
            return self._piece_to_name_pair[piece]
        except KeyError:
            raise RuntimeError(f"Not a known resource: {piece!r}")
