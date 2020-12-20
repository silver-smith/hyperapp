import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.client.object import ObjectType
from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .column import Column
from .tree_object import AppendItemDiff, InsertItemDiff, RemoveItemDiff, UpdateItemDiff, TreeObject
from .line_edit import LineObject
from .text_object import TextObject
from .record_object import RecordObject

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'name column_1 column_2')


class SampleTree(TreeObject):

    @classmethod
    def from_data(cls, state):
        return cls()

    @property
    def title(self):
        return 'Tree test'

    @property
    def data(self):
        return htypes.tree_view_sample.tree_view_sample_object()

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('column_1'),
            Column('column_2', type=tInt),
            ]

    async def fetch_items(self, path):
        log.info('SampleTree.fetch_items(%s)', path)
        if path and path[-1] == self._key(8):
            return
        self._distribute_fetch_results(path, [
            self._item(path, idx) for idx in range(5)])
        # signal there are no children for these paths
        for idx in range(4):
            self._distribute_fetch_results(list(path) + [self._key(idx * 2 + 1)], [])
        # check async population works
        await asyncio.sleep(0.3)
        self._distribute_fetch_results(path, [
            self._item(path, 5 + idx) for idx in range(3)])
        asyncio.get_event_loop().create_task(self._send_diffs(path))

    def _item(self, path, idx, suffix=''):
        return Item(
            name=self._key(idx),
            column_1='column 1 for /{} #{}'.format('/'.join(path), idx),
            column_2=f'{idx * 10}{suffix}',
            )

    def _key(self, idx):
        return 'item-{}'.format(idx)

    async def _send_diffs(self, path):
        await asyncio.sleep(0.3)
        self._distribute_diff(path, AppendItemDiff(self._item(path, 8)))
        self._distribute_diff([*path, self._key(3)], UpdateItemDiff(self._item(path, 3, suffix='/updated')))
        await asyncio.sleep(0.3)
        self._distribute_diff(path, InsertItemDiff(7, self._item(path, 9)))
        await asyncio.sleep(0.3)
        nested_path = list(path) + [self._key(9)]
        self._distribute_diff(nested_path, AppendItemDiff(self._item(nested_path, 10)))
        remove_path = list(path) + [self._key(5)]
        self._distribute_diff(remove_path, RemoveItemDiff())

    @command('open', kind='element')
    async def command_open(self, item_path):
        text = "Opened item {}".format('/'.join(item_path))
        return htypes.text.text(text)

    @command('edit', kind='element')
    async def _edit(self, item_path):
        return htypes.tree_view_sample.tree_sample_article(
            title=f"Article {item_path}",
            text=f"Sample contents for:\n{item_path}",
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
        return htypes.tree_view_sample.tree_sample_article(self._title, self._text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)

        sample_article_type = htypes.tree_view_sample.tree_view_sample_article_type(
            command_list=(),
            field_type_list=(
                htypes.record_object.record_type_field('title', services.ref_registry.distil(LineObject.type)),
                htypes.record_object.record_type_field('text', services.ref_registry.distil(TextObject.type)),
                ),
            )
        sample_tree_type = htypes.tree_view_sample.tree_view_sample_object_type(
            command_list=(
                htypes.object_type.object_command('open', services.ref_registry.distil(TextObject.type)),
                htypes.object_type.object_command('edit', services.ref_registry.distil(sample_article_type)),
                ),
            )
        SampleTree.type = sample_tree_type
        SampleArticle.type = sample_article_type

        services.object_registry.register_actor(htypes.tree_view_sample.tree_view_sample_object, SampleTree.from_data)
        services.object_registry.register_actor(htypes.tree_view_sample.tree_sample_article, SampleArticle.from_data, services.object_registry)

    @command('open_tree_view_sample')
    async def open_tree_view_sample(self):
        return htypes.tree_view_sample.tree_view_sample_object()

    @command('open_tree_view_sample_article')
    async def open_tree_view_sample_article(self):
        return htypes.tree_view_sample.tree_sample_article(
            title=f"Sample tree view article",
            text=f"Sample contents for:\nSample tree view article",
            )
