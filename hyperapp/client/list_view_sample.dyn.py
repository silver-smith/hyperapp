import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .list_object import ListObject

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'idx column_1 column_2')


class SampleObject(ListObject):

    @classmethod
    def from_state(cls, state):
        return cls()

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
        return htypes.text.text(text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.list_view_sample.list_view_sample_object, SampleObject.from_state)

    @command('open_list_view_sample')
    async def open_list_view_sample(self):
        return htypes.list_view_sample.list_view_sample_object()
