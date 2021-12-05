import asyncio
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .object_command import Command
from .list_object import ListFetcher, ListObject
from .simple_list_object import SimpleListObject


ITEM_FETCH_COUNT = 100

Item = namedtuple('Item', 'name visible')


class _Fetcher(ListFetcher):

    def __init__(self, object, columns_future):
        self._object = object
        self._columns_future = columns_future
        self._columns = []  # attr name list
        self._processed_item_count = 0

    def process_fetch_results(self, item_list, fetch_finished):
        key_attr = self._object.key_attribute
        self._update_columns(item_list)
        self._processed_item_count += len(item_list)
        if self._processed_item_count >= ITEM_FETCH_COUNT:
            self._send_result()
            return
        if item_list:
            from_key = getattr(item_list[-1], key_attr)
        else:
            from_key = None
        if fetch_finished and not self._columns_future.done():
            asyncio.ensure_future(self._object.fetch_items(from_key, self))

    def process_eof(self):
        self._send_result()

    def _send_result(self):
        if not self._columns_future.done():
            self._columns_future.set_result(self._columns)

    def _update_columns(self, new_item_list):
        seen_attrs = set()
        for item in new_item_list:
            seen_attrs |= set(
                name for name in dir(item)
                if not name.startswith('_') and not callable(getattr(item, name))
            )
        self._columns += list(seen_attrs - set(self._columns))


class ColumnList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.column_list.column_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        return cls(mosaic, lcs, object)

    def __init__(self, mosaic, lcs, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object

    @property
    def title(self):
        return f"Columns for: {self._object.title}"

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.column_list.column_list(piece_ref)

    @property
    def key_attribute(self):
        return 'name'

    async def get_all_items(self):
        columns_future = asyncio.Future()
        fetcher = _Fetcher(self._object, columns_future)
        asyncio.ensure_future(self._object.fetch_items(None, fetcher))
        column_attr_list = await columns_future
        return [
            Item(name, visible=True)
            for name in column_attr_list
            ]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.column_list.column_list,
            ColumnList.from_piece,
            services.mosaic,
            services.lcs,
            services.object_factory,
            )
        services.lcs.add(
            [*ListObject.dir_list[-1], htypes.command.object_commands_d()],
            htypes.column_list.column_list_command(),
            )
        services.command_registry.register_actor(
            htypes.column_list.column_list_command, Command.from_fn(self.name, self.column_list))

    async def column_list(self, object, view_state, origin_dir):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.column_list.column_list(piece_ref)
