import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .items_object import Column
from .list_object import ListObserver, ListObject

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

    async def fetch_items(self, from_key):
        if from_key is None:
            from_idx = 0
        else:
            from_idx = from_key + 1
        log.info('fetch_items from %r / #%d', from_key, from_idx)
        if from_idx > 100:
            log.info('  > already fetched')
            return
        log.info('  > distribute results')
        fetch_more = from_idx == 100
        self._distribute_fetch_results(
            [self._item(from_idx + idx) for idx in range(10)],
            fetch_finished=not fetch_more)
        if fetch_more:
            log.info('  > distribute more after 1 second')
            # check async population works
            await asyncio.sleep(1)
            log.info('  > distributing more and eof')
            self._distribute_fetch_results(
                [self._item(from_idx + 10 + idx) for idx in range(5)])
            self._distribute_eof()

    def _item(self, idx):
        return Item(
            idx=idx,
            column_1='column 1 for #{}'.format(idx),
            column_2=idx * 10,
            )

    @command('open', kind='element')
    async def command_open(self, item_key):
        text = "Opened item {}".format(item_key)
        object = htypes.text_object.text_object('text', text)
        return htypes.core.obj_handle('text_view', object)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SampleObject.impl_id, SampleObject.from_state)

    @command('open_list_view_sample')
    async def open_list_view_sample(self):
        object = htypes.core.object_base(SampleObject.impl_id)
        resource_key = resource_key_t(__module_ref__, ['SampleObject'])
        handle = htypes.core.int_list_handle('list', object, resource_key, key=2)
        return handle
