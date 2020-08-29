import abc
import asyncio
import logging
from dataclasses import dataclass

from hyperapp.common.util import single
from hyperapp.common.htypes import Type, tString
from hyperapp.client.object import ObjectType, ObjectObserver, Object
from hyperapp.client.module import ClientModule
from .column import Column

log = logging.getLogger(__name__)


class TreeObserver(ObjectObserver):

    def process_fetch_results(self, path, item_list):
        pass

    def process_diff(self, path, diff):
        pass


class Diff:
    pass


@dataclass
class AppendItemDiff(Diff):
    item: object


@dataclass
class InsertItemDiff(Diff):
    idx: int
    item: object


@dataclass
class RemoveItemDiff(Diff):
    pass


@dataclass
class UpdateItemDiff(Diff):
    item: object


class TreeObject(Object, metaclass=abc.ABCMeta):

    type = ObjectType(['tree'])
    category_list = ['tree']

    # return Column list
    @abc.abstractproperty
    def columns(self):
        pass

    @property
    def key_attribute(self):
        for column in self.columns:
            if column.is_key:
                return column.id
        raise RuntimeError("No key column or key_attribute is defined by class {}".format(self.__class__.__name__))

    class _Observer(TreeObserver):

        def __init__(self, item_future):
            self._item_future = item_future

        def process_fetch_results(self, path, item_list):
            if path:
                return  # Not our fetch - ours is from root.
            if item_list:
                self._item_future.set_result(item_list[0])
            else:
                self._item_future.set_result(None)

    async def _load_first_item(self):
        item_future = asyncio.Future()
        observer = self._Observer(item_future)
        self.subscribe(observer)
        asyncio.ensure_future(self.fetch_items([]))
        return await item_future

    async def first_item_key(self):
        item = await self._load_first_item()
        return [getattr(item, self.key_attribute)]

    @abc.abstractmethod
    async def fetch_items(self, path):
        pass

    def get_item_command_list(self, item_path):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_fetch_results(self, path, item_list):
        for observer in self._observers:
            log.debug('  Calling process_fetch_results for %s on %s/%s: %s', path, id(observer), observer, item_list)
            observer.process_fetch_results(path, item_list)

    def _distribute_diff(self, path, diff):
        for observer in self._observers:
            log.debug('  Calling process_diff for %s on %s/%s: %s', path, id(observer), observer, diff)
            observer.process_diff(path, diff)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.TreeObject = TreeObject
        services.Column = Column
