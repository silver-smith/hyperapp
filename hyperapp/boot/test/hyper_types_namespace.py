from types import SimpleNamespace


class HyperTypesNamespace:

    def __init__(self, pyobj_creg, types):
        self._pyobj_creg = pyobj_creg
        self._types = types  # Module name -> var name -> type mt piece.

    def __getattr__(self, name):
        if not name.startswith('_'):
            try:
                name_to_piece = self._types[name]
            except KeyError:
                pass
            else:
                return self._type_module_namespace(name_to_piece)
        raise RuntimeError(f"Unknown type module: {name!r}")

    def _type_module_namespace(self, name_to_piece):
        name_to_type = {}
        for name, piece in name_to_piece.items():
            name_to_type[name] = self._pyobj_creg.animate(piece)
        return SimpleNamespace(**name_to_type)
