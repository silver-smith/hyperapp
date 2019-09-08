from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        base = htypes.tree_view_sample.tree_view_sample_object()
        self._base_ref = services.ref_registry.register_object(base)

    @command('open_tree_to_list_adapter_sample')
    async def open_tree_to_list_adapter_sample(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._base_ref, ['item-2', 'item-4'])
