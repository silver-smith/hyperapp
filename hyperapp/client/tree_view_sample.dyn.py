import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import Column, TreeObject

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'name column_1 column_2')


class SampleObject(TreeObject):

    @classmethod
    def from_state(cls, state):
        return cls()

    def get_title(self):
        return 'Tree test'

    def get_columns(self):
        return [
            Column('name', is_key=True),
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
        return htypes.text.text(text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.tree_view_sample.tree_view_sample_object, SampleObject.from_state)

    @command('open_tree_view_sample')
    async def open_tree_view_sample(self):
        return htypes.tree_view_sample.tree_view_sample_object()
