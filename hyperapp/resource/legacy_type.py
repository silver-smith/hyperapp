import logging
from collections import defaultdict

log = logging.getLogger(__name__)


class LegacyTypeResourceModule:

    def __init__(self):
        self._name_to_piece = {}

    @property
    def name(self):
        return 'legacy_type'

    def __setitem__(self, name, type_piece):
        self._name_to_piece[name] = type_piece

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)

    @property
    def associations(self):
        return []


def add_builtin_types_to_pyobj_cache(pyobj_creg, builtin_types):
    for t in builtin_types.values():
        type_piece = pyobj_creg.actor_to_piece(t)
        pyobj_creg.add_to_cache(type_piece, t)


def convert_builtin_types_to_dict(pyobj_creg, builtin_types):
    name_to_module = defaultdict(dict)
    for t in builtin_types.values():
        type_piece = pyobj_creg.actor_to_piece(t)
        module_dict = name_to_module[t.module_name]
        module_dict[t.name] = type_piece
    return name_to_module


def load_legacy_type_resources(local_types):
    name_to_module = defaultdict(LegacyTypeResourceModule)
    for module_name, local_type_module in local_types.items():
        for name, type_piece in local_type_module.items():
            name_to_module[f'legacy_type.{module_name}'][name] = type_piece
            log.debug("Legacy type resource %s.%s: %s", module_name, name, type_piece)
    return name_to_module
