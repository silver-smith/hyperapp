import asyncio
import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .object_command import Command
from .list_object import ListFetcher, ListObject
from .tree_object import TreeObject
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


ITEM_FETCH_COUNT = 100

Item = namedtuple('Item', 'name ordered visible')


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
        self._columns += list(sorted(seen_attrs - set(self._columns)))


class ColumnList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.column_list.column_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        dir = [*object.dir_list[-1], htypes.column.column_list_d()]
        ordered_columns = lcs.get(dir)
        return cls(mosaic, lcs, object, ordered_columns)

    def __init__(self, mosaic, lcs, object, ordered_columns):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object
        self._ordered_columns = list(ordered_columns or [])
        self._item_attrs = None  # Lazy-loaded object item attributes.
        self._all_columns = []

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
        if self._item_attrs is None:
            columns_future = asyncio.Future()
            fetcher = _Fetcher(self._object, columns_future)
            asyncio.ensure_future(self._object.fetch_items(None, fetcher))
            self._item_attrs = await columns_future
            self._all_columns = self._ordered_columns + [
                name for name in self._item_attrs
                if name not in self._ordered_columns
            ]
        return [
            Item(
                name,
                ordered=name in self._ordered_columns,
                visible=self._get_visibility(name),
                )
            for name in self._all_columns
            ]

    @command
    async def swith_visibility(self, current_key):
        column_name = current_key
        dir = [*self._object.dir_list[-1], htypes.column.column_d(column_name), htypes.column.column_visible_d()]
        visible = self._get_visibility(column_name)
        if visible is False:
            visible = True
        else:  # True or None (not defined yet)
            visible = False
        log.info("Set column visibility to %r for: %s", visible, dir)
        self._lcs.set(dir, visible, persist=True)
        self.update()

    @command
    async def clear_visibility(self, current_key):
        column_name = current_key
        dir = [*self._object.dir_list[-1], htypes.column.column_d(column_name), htypes.column.column_visible_d()]
        self._lcs.remove(dir)
        self.update()

    @command
    async def move_up(self, current_key):
        column_name = current_key
        ordered_columns = self._all_columns
        idx = ordered_columns.index(column_name)
        if idx == 0:
            return
        del ordered_columns[idx]
        ordered_columns.insert(idx - 1, column_name)
        self._set_ordered_columns(ordered_columns)

    @command
    async def move_down(self, current_key):
        column_name = current_key
        ordered_columns = self._all_columns
        idx = ordered_columns.index(column_name)
        if idx == len(ordered_columns) - 1:
            return
        del ordered_columns[idx]
        ordered_columns.insert(idx + 1, column_name)
        self._set_ordered_columns(ordered_columns)

    def _get_visibility(self, column_name):
        dir = [*self._object.dir_list[-1], htypes.column.column_d(column_name), htypes.column.column_visible_d()]
        return self._lcs.get(dir)

    def _set_ordered_columns(self, ordered_columns):
        self._ordered_columns = ordered_columns
        dir = [*self._object.dir_list[-1], htypes.column.column_list_d()]
        self._lcs.set(dir, ordered_columns, persist=True)
        self.update()


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
        services.lcs.add(
            [*TreeObject.dir_list[-1], htypes.command.object_commands_d()],
            htypes.column_list.column_list_command(),
            )
        services.command_registry.register_actor(
            htypes.column_list.column_list_command, Command.from_fn(self.name, self.column_list))

    async def column_list(self, object, view_state, origin_dir):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.column_list.column_list(piece_ref)
