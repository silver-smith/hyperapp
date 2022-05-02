import logging
from collections import defaultdict

from hyperapp.common.module import Module

from . import htypes

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
        return set()


def make_legacy_type_resource_module(builtin_types, types, type_module_loader):
    name_to_module = defaultdict(LegacyTypeResourceModule)
    for t in builtin_types.values():
        type_ref = types.reverse_resolve(t)
        type_piece = htypes.legacy_type.type(type_ref)
        name_to_module[f'legacy_type.{t.module_name}'][t.name] = type_piece
        log.info("Legacy type resource %s.%s: %s", t.module_name, t.name, type_piece)
    for module_name, local_type_module in type_module_loader.registry.items():
        for name, type_ref in local_type_module.items():
            type_piece = htypes.legacy_type.type(type_ref)
            name_to_module[f'legacy_type.{module_name}'][name] = type_piece
            log.info("Legacy type resource %s.%s: %s", module_name, name, type_piece)
    return name_to_module


def python_object(piece, types):
    return types.resolve(piece.type_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        
        services.resource_module_registry.update(
            make_legacy_type_resource_module(services.builtin_types, services.types, services.type_module_loader))
        services.python_object_creg.register_actor(htypes.legacy_type.type, python_object, services.types)
