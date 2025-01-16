
class UnknownResourceName(Exception):
    pass


class ResourceRegistry:

    def __init__(self):
        self._name_pair_to_piece = {}
        self._piece_to_name_pair = {}
        self._module_registry = {}

    def __getitem__(self, name_pair):
        return self.resolve(name_pair)

    def __contains__(self, name_pair):
        try:
            is_cached, piece = self._resolve(name_pair)
        except KeyError:
            return False
        return True

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
        try:
            is_cached, piece = self._resolve(name_pair)
        except KeyError:
            raise UnknownResourceName(f"Unknown module or name: {name_pair[0]}.{name_pair[1]}")

    def resolve(self, name_pair):
        try:
            is_cached, piece = self._resolve(name_pair)
        except KeyError:
            raise RuntimeError(f"Error resolving {module_name}:{var_name}: Unknown module {module_name!r}")
        if not is_cached:
            self._name_pair_to_piece[name_pair] = piece
            self._piece_to_name_pair[piece] = name_pair
        return piece

    # Returns (is_cached, piece)
    def _resolve(self, name_pair):
        try:
            return (True, self._name_pair_to_piece[name_pair])
        except KeyError:
            pass
        module_name, var_name = name_pair
        module = self._module_registry[module_name]  # KeyError from here.
        return (False, module[var_name])  # or here.

    def has_piece(self, piece):
        return piece in self._piece_to_name_pair

    def reverse_resolve(self, piece):
        try:
            return self._piece_to_name_pair[piece]
        except KeyError:
            raise RuntimeError(f"Not a known resource: {piece!r}")
