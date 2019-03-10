from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import Column, TreeObserver, TreeObject

log = logging.getLogger(__name__)


MODULE_NAME = 'tree_view_sample'


Item = namedtuple('Item', 'name column_1 column_2')


class SampleObject(TreeObject):

    impl_id = 'sample-tree-object'

    @classmethod
    def from_state(cls, state):
        return cls()

    def get_columns(self):
        return [
            Column('name'),
            Column('column_1'),
            Column('column_2', type=tInt),
            ]

    async def fetch_items(self, path):
        self._notify_fetch_results(path, [
            Item('item-{}-{}'.format('.'.join(path), idx), 'column 1 for #%d' % idx, idx * 10)
            for idx in range(10)])


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SampleObject.impl_id, SampleObject.from_state)

    @command('open_tree_view_sample')
    async def open_tree_view_sample(self):
        object = htypes.core.object_base(SampleObject.impl_id)
        handle = htypes.tree_view.tree_handle('tree', object, None)
        return handle
