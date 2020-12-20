import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.object import ObjectType
from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .column import Column
from .list_object import ListObject
from .line_edit import LineObject
from .text_object import TextObject
from .record_object import RecordObject

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
    def data(self):
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

    @command('open', kind='element')
    async def command_open(self, item_key):
        text = "Opened item {}".format(item_key)
        return htypes.text.text(text)

    @command('edit', kind='element')
    async def _edit(self, item_key):
        return htypes.list_view_sample.list_sample_article(
            title=f"Article {item_key}",
            text=f"Sample contents for:\n{item_key}",
            )


class SampleArticle(RecordObject):

    @classmethod
    async def from_data(cls, state, object_registry):
        fields_pieces = {
            'title': htypes.line.line(state.title),
            'text': htypes.text.text(state.text),
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
    def data(self):
        return htypes.list_view_sample.list_sample_article(self._title, self._text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)

        sample_article_type = htypes.list_view_sample.list_view_sample_article_type(
            command_list=(),
            field_type_list=(
                htypes.record_object.record_type_field('title', services.ref_registry.distil(LineObject.type)),
                htypes.record_object.record_type_field('text', services.ref_registry.distil(TextObject.type)),
                ),
            )
        sample_list_type = htypes.list_view_sample.list_view_sample_object_type(
            command_list=(
                htypes.object_type.object_command('open', services.ref_registry.distil(TextObject.type)),
                htypes.object_type.object_command('edit', services.ref_registry.distil(sample_article_type)),
                ),
            )
        SampleList.type = sample_list_type
        SampleArticle.type = sample_article_type

        services.object_registry.register_actor(htypes.list_view_sample.list_view_sample_object, SampleList.from_data)
        services.object_registry.register_actor(htypes.list_view_sample.list_sample_article, SampleArticle.from_data, services.object_registry)

    @command('open_list_view_sample')
    async def open_list_view_sample(self):
        return htypes.list_view_sample.list_view_sample_object()
