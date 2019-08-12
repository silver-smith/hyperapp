from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.module import ClientModule
from .log_viewer import SessionLogs
from .master_details import MasterDetailsView


class ViewProducer:

    def __init__(self, type_resolver, resource_resolver, object_registry, view_producer_registry):
        self._type_resolver = type_resolver
        self._resource_resolver = resource_resolver
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._locale = 'en'

    async def produce_view(self, state, object, observer=None):
        type_ref = self._state_type_ref(state)
        if isinstance(object, SessionLogs):
            return await self._make_session_logs(type_ref, object, observer)
        return (await self._view_producer_registry.produce_view(type_ref, object, observer))

    async def _make_session_logs(self, type_ref, object, observer):
        master = await self._view_producer_registry.produce_view(type_ref, object, observer)
        details_command = object.get_command('open')
        return MasterDetailsView(self._object_registry, self, master, details_command)

    def _state_type_ref(self, state):
        current_t = deduce_value_type(state)
        return self._type_resolver.reverse_resolve(current_t)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_producer = ViewProducer(
            services.type_resolver,
            services.resource_resolver,
            services.object_registry,
            services.view_producer_registry,
            )
