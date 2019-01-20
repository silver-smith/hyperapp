from hyperapp.client.list_view import ListView
from hyperapp.client.module import ClientModule
from . import htypes


MODULE_NAME = 'list_view'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.view_registry.register('list', self._list_view_from_state, services.objimpl_registry, services.resources_manager)

    @classmethod
    async def _list_view_from_state(self, locale, state, parent, objimpl_registry, resources_manager):
        data_type = htypes.core.handle.get_object_class(state)
        object = await objimpl_registry.resolve_async(state.object)
        return ListView(locale, parent, resources_manager, state.resource_id, data_type, object, state.key, state.sort_column_id)
