import abc
import asyncio
import logging
from dataclasses import dataclass

from hyperapp.common.module import Module

from . import htypes
from .ui_object import ObjectObserver, Object

log = logging.getLogger(__name__)


class TreeFetcher:

    @abc.abstractmethod
    def process_fetch_results(self, path, item_list):
        pass


class TreeObserver(ObjectObserver):

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

    view_state_fields = ['current_key']
    dir_list = [
        *Object.dir_list,
        [htypes.tree_object.tree_object_d()],
        ]

    def make_state(self, current_key):
        if type(current_key[0]) is int:
            return htypes.tree_object.int_state(current_key)
        if type(current_key[0]) is str:
            return htypes.tree_object.string_state(current_key)
        raise RuntimeError(f"{self.__class__.__name__}: Unsupported key type: {type(current_key)}")

    @abc.abstractproperty
    def key_attribute(self):
        pass

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
    async def fetch_items(self, path, fetcher):
        pass

    def get_item_command_list(self, item_path):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_diff(self, path, diff):
        for observer in self._observers:
            log.debug('  Calling process_diff for %s on %s/%s: %s', path, id(observer), observer, diff)
            observer.process_diff(path, diff)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.TreeObject = TreeObject
