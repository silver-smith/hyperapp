import logging
import abc
import asyncio
from functools import total_ordering

from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import Type, tString
from hyperapp.client.object import ObjectType, ObjectObserver, Object

log = logging.getLogger(__name__)


class ListDiff(object):

    @classmethod
    def add_one(cls, element):
        return cls([], [element])

    @classmethod
    def add_many(cls, elements):
        return cls([], elements)

    @classmethod
    def replace(cls, key, element):
        return cls([key], [element])

    @classmethod
    def delete(cls, key):
        return cls([key], [])

    @classmethod
    def from_data(cls, iface, rec):
        return cls(rec.remove_keys, [Element.from_data(iface, element) for element in rec.elements])

    def __init__(self, remove_keys, elements):
        assert isinstance(remove_keys, list), repr(remove_keys)
        assert is_list_inst(elements, Element), repr(elements)
        self.remove_keys = remove_keys
        self.elements = elements

    def __repr__(self):
        return 'ListDiff(-%r+%r)' % (self.remove_keys, self.elements)

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        return iface.Diff(self.remove_keys, [element.to_data(iface) for element in self.elements])


class ListObserver(ObjectObserver):

    def process_fetch_results(self, item_list, fetch_finished):
        pass

    def process_eof(self):
        pass

    def process_diff(self, diff):
        pass


class ListObject(Object, metaclass=abc.ABCMeta):

    type = ObjectType(['list'])
    category_list = ['list']

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

    class _Observer(ListObserver):

        def __init__(self, object, item_future):
            self._object = object
            self._item_future = item_future

        def process_fetch_results(self, item_list, fetch_finished):
            if item_list:
                self._item_future.set_result(item_list[0])
            elif not fetch_finished:
                asyncio.ensure_future(self._object.fetch_items(None))
            else:
                self._item_future.set_result(None)

        def process_eof(self):
            self._item_future.set_result(None)

    async def _load_first_item(self):
        item_future = asyncio.Future()
        observer = self._Observer(self, item_future)
        self.subscribe(observer)
        asyncio.ensure_future(self.fetch_items(None))
        return await item_future

    async def first_item_key(self):
        item = await self._load_first_item()
        return getattr(item, self.key_attribute)
        
    @abc.abstractmethod
    async def fetch_items(self, from_key):
        pass

    def get_item_command_list(self, item_key):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_fetch_results(self, item_list, fetch_finished=True):
        for observer in self._observers:
            log.debug('  Calling process_fetch_results on %s/%s', id(observer), observer)
            observer.process_fetch_results(item_list, fetch_finished)

    def _distribute_eof(self):
        for observer in self._observers:
            log.debug('  Calling eof on %s/%s', id(observer), observer)
            observer.process_eof()

    # def __del__(self):
    #     log.debug('~list_object self=%s', id(self))
