import asyncio
from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt

from . import htypes
from .command import command
from .ui_object import ObjectType
from .tree_object import AppendItemDiff, InsertItemDiff, RemoveItemDiff, UpdateItemDiff, TreeObject
from .string_object import StringObject
from .record_object import RecordObject
from .module import ClientModule

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'name column_1 column_2')


class SampleTree(TreeObject):

    dir_list = [
        *TreeObject.dir_list,
        [htypes.tree_view_sample.tree_view_sample_d()],
        ]

    @classmethod
    def from_data(cls, state):
        return cls()

    @property
    def title(self):
        return 'Tree test'

    @property
    def piece(self):
        return htypes.tree_view_sample.tree_view_sample_object()

    @property
    def key_attribute(self):
        return 'name'

    async def fetch_items(self, path):
        log.info('SampleTree.fetch_items(%s)', path)
        if path and path[-1] == self._key(8):
            return
        self._distribute_fetch_results(path, [
            self._item(path, idx) for idx in range(5)])
        # signal there are no children for these paths
        for idx in range(4):
            self._distribute_fetch_results([*path, self._key(idx * 2 + 1)], [])
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
        nested_path = [*path, self._key(9)]
        self._distribute_diff(nested_path, AppendItemDiff(self._item(nested_path, 10)))
        remove_path = [*path, self._key(5)]
        self._distribute_diff(remove_path, RemoveItemDiff())

    @command
    async def open(self, current_key):
        text = "Opened item {}".format('/'.join(current_key))
        return text

    @command
    async def edit(self, current_key):
        return htypes.tree_view_sample.tree_sample_article(
            title=f"Article {current_key}",
            text=f"Sample contents for:\n{current_key}",
            )


class SampleArticle(RecordObject):

    dir_list = [
        *RecordObject.dir_list,
        [htypes.tree_view_sample.tree_view_sample_article_d()],
        ]

    @classmethod
    async def from_data(cls, state, object_factory):
        fields_pieces = {
            'title': state.title,
            'text': state.text,
            }
        self = cls(state.title, state.text)
        await self.async_init(object_factory, fields_pieces)
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
        return htypes.tree_view_sample.tree_sample_article(self._title, self._text)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(htypes.tree_view_sample.tree_view_sample_object, SampleTree.from_data)
        services.object_registry.register_actor(htypes.tree_view_sample.tree_sample_article, SampleArticle.from_data, services.object_factory)

    @command
    async def open_tree_view_sample(self):
        return htypes.tree_view_sample.tree_view_sample_object()

    @command
    async def open_tree_view_sample_article(self):
        return htypes.tree_view_sample.tree_sample_article(
            title=f"Sample tree view article",
            text=f"Sample contents for:\nSample tree view article",
            )
