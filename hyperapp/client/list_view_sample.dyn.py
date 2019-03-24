import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .list_object import Column, ListObserver, ListObject

log = logging.getLogger(__name__)


MODULE_NAME = 'list_view_sample'


Item = namedtuple('Item', 'idx column_1 column_2')


class SampleObject(ListObject):

    impl_id = 'sample-list-object'

    @classmethod
    def from_state(cls, state):
        return cls()

    def get_state(self):
        return htypes.core.object_base(self.impl_id)

    def get_title(self):
        return 'List test'

    def get_columns(self):
        return [
            Column('idx', type=tInt, is_key=True),
            Column('column_1'),
            Column('column_2', type=tInt),
            ]

    async def fetch_items(self):
        log.info('SampleObject.fetch_items')
        self._distribute_fetch_results([
            self._item(idx) for idx in range(10)])
        # check async population works
        await asyncio.sleep(1)
        self._distribute_fetch_results([
            self._item(5 + idx) for idx in range(5)])

    def _item(self, idx):
        return Item(
            idx=idx,
            column_1='column 1 for #{}'.format(idx),
            column_2=idx * 10,
            )


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SampleObject.impl_id, SampleObject.from_state)

    @command('open_list_view_sample')
    async def open_list_view_sample(self):
        object = htypes.core.object_base(SampleObject.impl_id)
        resource_key = resource_key_t(__module_ref__, ['list'])
        handle = htypes.core.int_list_handle('list', object, resource_key, key=2)
        return handle
