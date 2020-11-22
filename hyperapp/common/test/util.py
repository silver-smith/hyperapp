from ..route_storage import RouteRepository


class PhonyRouteRepository(RouteRepository):

    def enumerate(self):
        return []

    def add(self, public_key, routes):
        pass


def resolve_type(services, module, name):
    type_ref = services.local_type_module_registry[module][name]
    return services.types.resolve(type_ref)
