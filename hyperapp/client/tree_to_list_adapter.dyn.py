# Provide list view interface to tree view object

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, VisualItem, Layout
from .list_object import ListObject
from .tree_object import TreeObserver, TreeObject


class _Observer(TreeObserver):

    def __init__(self, adapter):
        self._adapter = adapter

    def process_fetch_results(self, path, item_list):
        self._adapter._process_tree_fetch_results(path, item_list)


class TreeToListAdapter(ListObject):

    @classmethod
    async def from_state(cls, state, object_resolver):
        tree_object = await object_resolver.resolve(state.base_ref)
        return cls(state.base_ref, tree_object, state.path)

    def __init__(self, base_ref, tree_object, path):
        self._base_ref = base_ref
        self._tree_object = tree_object
        self._path = list(path)  # accept tuples as well
        super().__init__()
        self._observer = _Observer(self)
        self._tree_object.subscribe(self._observer)

    def get_title(self):
        return '%s:/%s' % (self._tree_object.get_title(), '/'.join(str(item) for item in self._path))

    @property
    def data(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._base_ref, self._path)

    def get_columns(self):
        return self._tree_object.get_columns()

    @property
    def key_attribute(self):
        return self._tree_object.key_attribute

    async def fetch_items(self, from_key):
        assert from_key is None  # We always return full list
        await self._tree_object.fetch_items(self._path)

    def _process_tree_fetch_results(self, path, item_list):
        if list(path) != self._path:  # path may also be tuple
            return  # Not our path, not our request
        self._distribute_fetch_results(item_list, fetch_finished=True)
        self._distribute_eof()

    # todo: distinguish leaf items, do not open them
    @command('open', kind='element')
    async def command_open(self, item_key):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._base_ref, self._path + [item_key])

    @command('open_parent')
    async def command_open_parent(self):
        if not self._path:
            return
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._base_ref, self._path[:-1])


class TreeToListLayout(Layout):

    def __init__(self, base_list_layout, path):
        super().__init__(path)
        self._base_list_layout = base_list_layout

    @property
    def data(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter_layout()

    def get_view_ref(self):
        assert 0  # todo: remove

    async def create_view(self):
        return (await self._base_list_layout.create_view())

    async def visual_item(self):
        base_item = await self._base_list_layout.visual_item()
        return RootVisualItem('TreeToListAdapter', children=[
            base_item.to_item(0, 'base'),
            ])


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        self._object_layout_producer = services.object_layout_producer
        services.object_registry.register_type(
            htypes.tree_to_list_adapter.tree_to_list_adapter, TreeToListAdapter.from_state, services.object_resolver)
        services.available_object_layouts.register('as_list', TreeObject.category_list, self._make_layout_rec)
        services.object_layout_registry.register_type(htypes.tree_to_list_adapter.tree_to_list_adapter_layout, self._produce_layout)

    async def _make_layout_rec(self, object):
        return htypes.tree_to_list_adapter.tree_to_list_adapter_layout()

    async def _produce_layout(self, state, object, command_hub, piece_opener):
        base_object_ref = self._ref_registry.register_object(object.data)
        adapter = TreeToListAdapter(base_object_ref, object, path=[])
        base_list_layout = await self._object_layout_producer.produce_layout(adapter, command_hub, piece_opener)
        return TreeToListLayout(base_list_layout, path=[])
