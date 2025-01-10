import logging

from hyperapp.boot.htypes.builtin_service import builtin_service_t

log = logging.getLogger(__name__)


class BuiltinServiceResourceModule:

    def __init__(self, name_to_piece):
        self._name_to_piece = name_to_piece

    @property
    def name(self):
        return 'builtins'

    def __setitem__(self, name, service_piece):
        self._name_to_piece[name] = service_piece

    def __contains__(self, var_name):
        return var_name in self._name_to_piece

    def __getitem__(self, var_name):
        return self._name_to_piece[var_name]

    def __iter__(self):
        return iter(self._name_to_piece)

    def merge_with(self, other):
        assert isinstance(other, BuiltinServiceResourceModule)
        return BuiltinServiceResourceModule({
            **self._name_to_piece,
            **other._name_to_piece,
            })


def add_builtin_services_to_pyobj_cache(services, builtin_services, pyobj_creg):
    for service_name in builtin_services:
        piece = builtin_service_t(service_name)
        service = getattr(services, service_name)
        pyobj_creg.add_to_cache(piece, service)


def make_builtin_service_resource_module(mosaic, builtin_services, resource_registry):
    name_to_piece = {}

    for service_name in builtin_services:
        piece = builtin_service_t(service_name)
        name_to_piece[f'{service_name}.service'] = piece
        log.debug("Builtin service resource %r: %s", service_name, piece)

    for name, piece in name_to_piece.items():
        resource_registry.add_to_cache(('builtins', name), piece)
    return BuiltinServiceResourceModule(name_to_piece)


def builtin_service_pyobj(piece, services):
    return getattr(services, piece.name)
