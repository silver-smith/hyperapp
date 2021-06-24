import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t

from . import htypes
from .object_command import command
from .object import ObjectType
from .column import Column
from .list_object import ListObject
from .string_object import StringObject
from .record_object import RecordObject
from .module import ClientModule, global_command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'idx column_1 column_2')


class SampleList(ListObject):

    @classmethod
    def from_data(cls, state):
        return cls()

    @property
    def title(self):
        return 'List test'

    @property
    def piece(self):
        return htypes.list_view_sample.list_view_sample_object()

    @property
    def columns(self):
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

    @command
    async def open(self, current_key):
        text = "Opened item {}".format(current_key)
        return text

    @command
    async def edit(self, current_key):
        return htypes.list_view_sample.list_sample_article(
            title=f"Article {current_key}",
            text=f"Sample contents for:\n{current_key}",
            )


class SampleArticle(RecordObject):

    @classmethod
    async def from_data(cls, state, object_registry):
        fields_pieces = {
            'title': state.title,
            'text': state.text,
            }
        self = cls(state.title, state.text)
        await self.async_init(object_registry, fields_pieces)
        return self

    def __init__(self, title, text):
        super().__init__()
        self._title = title
        self._text = text

    @property
    def title(self):
        return f"Sample list view article: {self._title}"

    @property
    def piece(self):
        return htypes.list_view_sample.list_sample_article(self._title, self._text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(htypes.list_view_sample.list_view_sample_object, SampleList.from_data)
        # services.object_registry.register_actor(htypes.list_view_sample.list_sample_article, SampleArticle.from_data, services.object_registry)

    @global_command('open_list_view_sample')
    async def open_list_view_sample(self):
        return htypes.list_view_sample.list_view_sample_object()
