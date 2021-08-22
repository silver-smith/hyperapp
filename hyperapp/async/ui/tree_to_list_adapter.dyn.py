# Provide list view interface to tree view object

import logging
import weakref

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .list_object import ListObject
from .tree_object import TreeObserver, TreeObject

log = logging.getLogger(__name__)


class _Observer(TreeObserver):

    def __init__(self, adapter):
        self._adapter = adapter

    def process_fetch_results(self, path, item_list):
        self._adapter._process_tree_fetch_results(path, item_list)


class TreeToListAdapter(ListObject):

    dir_list = [
        *ListObject.dir_list,
        [htypes.tree_to_list_adapter.tree_to_list_adapter_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, object_factory):
        tree_object = await object_factory.invite(piece.base_ref)
        return cls(mosaic, tree_object, piece.path)

    def __init__(self, mosaic, tree_object, path):
        super().__init__()
        self._mosaic = mosaic
        self._tree_object = tree_object
        self._path = list(path)  # accept tuples as well
        self._observer = _Observer(self)
        self._tree_object.subscribe(self._observer)

    @property
    def title(self):
        path_str = '/'.join(str(item) for item in self._path)
        return f"{self._tree_object.title}:/{path_str}"

    @property
    def piece(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path)

    @property
    def command_list(self):
        return [
            *self._tree_object.command_list,
            *super().command_list,
            ]

    @property
    def columns(self):
        return self._tree_object.columns

    @property
    def key_attribute(self):
        return self._tree_object.key_attribute

    async def fetch_items(self, from_key):
        assert from_key is None, repr(from_key)  # We always return full list
        await self._tree_object.fetch_items(self._path)

    @property
    def base_object(self):
        return self._tree_object

    @property
    def current_path(self):
        return self._path

    @property
    def _tree_object_ref(self):
        return self._mosaic.put(self._tree_object.piece)

    def _process_tree_fetch_results(self, path, item_list):
        if list(path) != self._path:  # path may also be tuple
            return  # Not our path, not our request
        self._distribute_fetch_results(item_list, fetch_finished=True)
        self._distribute_eof()

    # todo: distinguish leaf items, do not open them
    @command
    async def enter(self, current_key):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path + [current_key])

    @command
    async def parent(self):
        if not self._path:
            return
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._tree_object_ref, self._path[:-1])


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry.register_actor(
            htypes.tree_to_list_adapter.tree_to_list_adapter,
            TreeToListAdapter.from_piece,
            services.mosaic,
            services.object_factory,
            )
        services.lcs.add(
            [htypes.view.view_d('available'), *TreeObject.dir_list[-1]],
            htypes.tree_to_list_adapter.tree_to_list_adapter_view(),
            )
        services.view_registry.register_actor(
            htypes.tree_to_list_adapter.tree_to_list_adapter_view, self._open_adapter_view, services.mosaic, services.view_producer)

    async def _open_adapter_view(self, piece, object, add_dir_list, mosaic, view_producer):
        adapter = TreeToListAdapter(mosaic, object, path=[])
        return await view_producer.create_view(adapter)
