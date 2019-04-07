import logging
import abc
import asyncio
from functools import total_ordering

from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import Type, tString
from hyperapp.client.commander import Command
from hyperapp.client.object import ObjectObserver, Object

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


class Column(object):

    def __init__(self, id, type=tString, is_key=False):
        assert isinstance(id, str), repr(id)
        assert isinstance(type, Type), repr(type)
        assert isinstance(is_key, bool), repr(is_key)
        self.id = id
        self.type = type
        self.is_key = is_key

    def __eq__(self, other):
        assert isinstance(other, Column), repr(other)
        return (other.id == self.id and
                other.type == self.type and
                other.is_key == self.is_key)

    def __hash__(self):
        return hash((self.id, self.type, self.is_key))


class ListObserver(ObjectObserver):

    def process_fetch_results(self, item_list):
        pass

    def process_eof(self):
        pass

    def process_diff(self, diff):
        pass


class ListObject(Object, metaclass=abc.ABCMeta):

    # return Column list
    @abc.abstractmethod
    def get_columns(self):
        pass

    @abc.abstractmethod
    async def fetch_items(self, from_idx):
        pass

    def get_item_command_list(self, item_id):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_fetch_results(self, item_list, fetch_finished=True):
        for observer in self._observers:
            log.debug('  Calling process_fetch_results on %s/%s', id(observer), observer)
            observer.process_fetch_results(item_list, fetch_finished)

    def _distribute_eof(self):
        for observer in self._observers:
            log.debug('  Calling eof on %s/%s', id(observer), observer)
            observer.process_eof()

    def __del__(self):
        log.debug('~list_object self=%s', id(self))
