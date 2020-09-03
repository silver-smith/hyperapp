# Provide list view interface to tree view object

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .layout import ObjectLayout
from .list_object import ListObject
from .tree_object import TreeObserver, TreeObject


class _Observer(TreeObserver):

    def __init__(self, adapter):
        self._adapter = adapter

    def process_fetch_results(self, path, item_list):
        self._adapter._process_tree_fetch_results(path, item_list)


class TreeToListAdapter(ListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, object_resolver):
        tree_object = await object_resolver.resolve(state.base_ref)
        return cls(ref_registry, tree_object, state.path)

    def __init__(self, ref_registry, tree_object, path):
        self._ref_registry = ref_registry
        self._tree_object = tree_object
        self._path = list(path)  # accept tuples as well
        super().__init__()
        self._observer = _Observer(self)
        self._tree_object.subscribe(self._observer)

    @property
    def title(self):
        return '%s:/%s' % (self._tree_object.title, '/'.join(str(item) for item in self._path))

    @property
    def data(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path)

    @property
    def columns(self):
        return self._tree_object.columns

    @property
    def key_attribute(self):
        return self._tree_object.key_attribute

    async def fetch_items(self, from_key):
        assert from_key is None  # We always return full list
        await self._tree_object.fetch_items(self._path)

    @property
    def base_object(self):
        return self._tree_object

    @property
    def _tree_object_ref(self):
        return self._ref_registry.register_object(self._tree_object.data)

    def _process_tree_fetch_results(self, path, item_list):
        if list(path) != self._path:  # path may also be tuple
            return  # Not our path, not our request
        self._distribute_fetch_results(item_list, fetch_finished=True)
        self._distribute_eof()

    # todo: distinguish leaf items, do not open them
    @command('open', kind='element')
    async def command_open(self, item_key):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path + [item_key])

    @command('open_parent')
    async def command_open_parent(self):
        if not self._path:
            return
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path[:-1])


class TreeToListLayout(ObjectLayout):

    @classmethod
    async def from_data(cls, state, path, layout_watcher, ref_registry, object_layout_registry, default_object_layouts):
        object_type = await async_ref_resolver.resolve_ref_to_object(state.object_type_ref)
        base_list_layout = await default_object_layouts.construct_default_layout(
            object_type, layout_watcher, object_layout_registry, path=[*path, 'base'])
        return cls(ref_registry, base_list_layout, path, object_type, state.command_list)

    def __init__(self, ref_registry, base_list_layout, path, object_type, command_list_data):
        super().__init__(path, object_type, command_list_data)
        self._ref_registry = ref_registry
        self._base_list_layout = base_list_layout

    @property
    def data(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter_layout(self._object_type_ref, self._command_list_data)

    async def create_view(self, command_hub, object):
        adapter = TreeToListAdapter(self._ref_registry, object, path=[])
        return (await self._base_list_layout.create_view(command_hub, adapter))

    async def visual_item(self):
        base_item = await self._base_list_layout.visual_item()
        return self.make_visual_item('TreeToListAdapter', children=[base_item])

    def get_current_commands(self, object, view):
        return self._base_list_layout.get_current_commands(object.base_object, view)

    def get_item_commands(self, object, item_key):
        return self._base_list_layout.get_item_commands(object.base_object, item_key)

    def available_code_commands(self, object):
        return [
            *super().collect_view_commands(),
            *self._base_list_layout.available_code_commands(object.base_object),
            *[(tuple(self._path), command) for command in object.get_all_command_list()],
            ]


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        services.object_registry.register_type(
            htypes.tree_to_list_adapter.tree_to_list_adapter, TreeToListAdapter.from_state, services.ref_registry, services.object_resolver)
        services.available_object_layouts.register('as_list', [TreeObject.type._t], self._make_layout_data)
        services.object_layout_registry.register_type(
            htypes.tree_to_list_adapter.tree_to_list_adapter_layout, TreeToListLayout.from_data,
            services.ref_registry, services.object_layout_registry, services.default_object_layouts)

    async def _make_layout_data(self, object_type):
        object_type_ref = self._ref_registry.register_object(object_type)
        command_list = ObjectLayout.make_default_command_list(object)
        return htypes.tree_to_list_adapter.tree_to_list_adapter_layout(object_type_ref, command_list)
