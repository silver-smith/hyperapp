import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import Column, TreeObject

log = logging.getLogger(__name__)


MODULE_NAME = 'tree_view_sample'


Item = namedtuple('Item', 'name column_1 column_2')


class SampleObject(TreeObject):

    impl_id = 'sample-tree-object'

    @classmethod
    def from_state(cls, state):
        return cls()

    def get_state(self):
        return htypes.core.object_base(self.impl_id)

    def get_title(self):
        return 'Tree test'

    def get_columns(self):
        return [
            Column('name'),
            Column('column_1'),
            Column('column_2', type=tInt),
            ]

    async def fetch_items(self, path):
        log.info('SampleObject.fetch_items(%s)', path)
        self._distribute_fetch_results(path, [
            self._item(path, idx) for idx in range(5)])
        # signal there are no children for these paths
        for idx in range(4):
            self._distribute_fetch_results(list(path) + [self._key(idx * 2 + 1)], [])
        # check async population works
        await asyncio.sleep(1)
        self._distribute_fetch_results(path, [
            self._item(path, 5 + idx) for idx in range(3)])

    def _item(self, path, idx):
        return Item(
            name=self._key(idx),
            column_1='column 1 for /{} #{}'.format('/'.join(path), idx),
            column_2=idx * 10,
            )

    def _key(self, idx):
        return 'item-{}'.format(idx)

    @command('open', kind='element')
    async def command_open(self, item_path):
        text = "Opened item {}".format('/'.join(item_path))
        object = htypes.text_object.text_object('text', text)
        return htypes.core.obj_handle('text_view', object)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SampleObject.impl_id, SampleObject.from_state)

    @command('open_tree_view_sample')
    async def open_tree_view_sample(self):
        object = htypes.core.object_base(SampleObject.impl_id)
        resource_key = resource_key_t(__module_ref__, ['SampleObject'])
        handle = htypes.tree_view.string_tree_handle('tree', object, resource_key, current_path=['item-1', 'item-2'])
        return handle
