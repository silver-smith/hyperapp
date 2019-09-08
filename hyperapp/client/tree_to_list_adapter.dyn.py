# Provide list view interface to tree view object

from hyperapp.client.module import ClientModule
from . import htypes
from .list_object import ListObject
from .tree_object import TreeObserver


class _Observer(TreeObserver):

    def __init__(self, adapter):
        self._adapter = adapter

    def process_fetch_results(self, path, item_list):
        self._adapter._process_tree_fetch_results(path, item_list)


class TreeToListAdapter(ListObject):

    @classmethod
    async def from_state(cls, state, object_resolver):
        tree_object = await object_resolver.resolve(state.base_ref)
        return cls(tree_object, state.path)

    def __init__(self, tree_object, path):
        self._tree_object = tree_object
        self._path = path
        super().__init__()
        self._observer = _Observer(self)
        self._tree_object.subscribe(self._observer)

    def get_title(self):
        return '%s:/%s' % (self._tree_object.get_title(), '/'.join(self._path))

    def get_columns(self):
        return self._tree_object.get_columns()

    async def fetch_items(self, from_key):
        assert from_key is None  # We always return full list
        await self._tree_object.fetch_items(self._path)

    def _process_tree_fetch_results(self, path, item_list):
        if path != self._path:
            return  # Not our path, not our request
        self._distribute_fetch_results(item_list, fetch_finished=True)
        self._distribute_eof()

    # @command('open', kind='element')
    # async def command_open(self, item_key):
    #     text = "Opened item {}".format(item_key)
    #     return htypes.text.text(text)

    # @command('open_parent')
    # async def command_open_parent(self):
    #     if not self._path:
    #         return
    #     path = self._path[:-1]
    #     return (await self._open_path(path, current_file_name=self._path[-1]))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.tree_to_list_adapter.tree_to_list_adapter, TreeToListAdapter.from_state, services.object_resolver)
