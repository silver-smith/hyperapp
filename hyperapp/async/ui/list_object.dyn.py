import logging
import abc
import asyncio
from collections import namedtuple
from dataclasses import dataclass
from functools import cached_property, total_ordering
from typing import List

from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import Type, tInt, tString

from . import htypes
from .ui_object import ObjectObserver, Object

log = logging.getLogger(__name__)


@dataclass
class ListDiff:
    remove_keys: List[object]
    items: List[object]

    @classmethod
    def add_one(cls, item):
        return cls([], [item])

    @classmethod
    def add_many(cls, item_list):
        return cls([], item_list)

    @classmethod
    def replace(cls, key, item):
        return cls([key], [item])

    @classmethod
    def delete(cls, key):
        return cls([key], [])

    def __repr__(self):
        return 'ListDiff(-%r+%r)' % (self.remove_keys, self.items)


class ListObserver(ObjectObserver):

    def process_diff(self, diff):
        pass


class ListFetcher:

    @abc.abstractmethod
    def process_fetch_results(self, item_list, fetch_finished):
        pass

    @abc.abstractmethod
    def process_eof(self):
        pass


class ListObject(Object, metaclass=abc.ABCMeta):

    view_state_fields = ['current_key']
    dir_list = [
        *Object.dir_list,
        [htypes.list_object.list_object_d()],
        ]

    # todo: construct state from key column type on-the-fly.
    @cached_property
    def State(self):
        if self._key_column.type is tInt:
            return htypes.list_object.int_state
        if self._key_column.type is tString:
            return htypes.list_object.string_state
        raise RuntimeError(f"{self.__class__.__name__}: Unsupported column type: {self._key_column.type}")
        
    # return Column list
    @abc.abstractproperty
    def columns(self):
        pass

    @cached_property
    def _key_column(self):
        for column in self.columns:
            if column.is_key:
                return column
        raise RuntimeError(f"No key column or key_attribute is defined by class {self.__class__.__name__}")

    @property
    def key_attribute(self):
        return self._key_column.id

    class _Fetcher(ListFetcher):

        def __init__(self, object, wanted_key, item_future):
            self._object = object
            self._wanted_key = wanted_key
            self._item_future = item_future

        def process_fetch_results(self, item_list, fetch_finished):
            key_attr = self._object.key_attribute
            for item in item_list:
                if getattr(item, key_attr) == self._wanted_key:
                    self._item_future.set_result(item)
                    return
            if item_list:
                from_key = getattr(item_list[-1], key_attr)
            else:
                from_key = None
            if fetch_finished and not self._item_future.done():
                asyncio.ensure_future(self._object.fetch_items(from_key, self))

        def process_eof(self):
            if not self._item_future.done():
                self._item_future.set_result(None)

    async def item_by_key(self, key):
        item_future = asyncio.Future()
        fetcher = self._Fetcher(self, key, item_future)
        asyncio.ensure_future(self.fetch_items(None, fetcher))
        return await item_future
        
    @abc.abstractmethod
    async def fetch_items(self, from_key, fetcher):
        pass

    def get_item_command_list(self, item_key):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_diff(self, diff):
        for observer in self._observers:
            log.debug('  Calling process_diff on %s/%s: %s', id(observer), observer, diff)
            observer.process_diff(diff)
