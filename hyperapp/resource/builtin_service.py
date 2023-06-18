import logging

from hyperapp.common.htypes.builtin_service import legacy_service_t

log = logging.getLogger(__name__)


class LegacyServiceResourceModule:

    def __init__(self, name_to_piece):
        self._name_to_piece = name_to_piece

    @property
    def name(self):
        return 'legacy_service'

    def __setitem__(self, name, service_piece):
        self._name_to_piece[name] = service_piece

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)

    @property
    def associations(self):
        return set()

    def merge_with(self, other):
        assert isinstance(other, LegacyServiceResourceModule)
        return LegacyServiceResourceModule({
            **self._name_to_piece,
            **other._name_to_piece,
            })


def make_legacy_service_resource_module(mosaic, builtin_services, resource_registry):
    name_to_piece = {}

    for service_name in builtin_services:
        piece = legacy_service_t(service_name)
        name_to_piece[service_name] = piece
        log.info("Builtin legacy service resource %r: %s", service_name, piece)

    for name, piece in name_to_piece.items():
        resource_registry.add_to_cache(('legacy_service', name), piece)
    return LegacyServiceResourceModule(name_to_piece)


def builtin_service_python_object(piece, services):
    return getattr(services, piece.name)
