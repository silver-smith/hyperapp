import logging
import abc
import asyncio
from functools import total_ordering
from PySide import QtCore, QtGui

from ..common.util import is_list_inst, dt2local_str
from ..common.htypes import Type, tString
from .diff import Diff
from .command_class import Command
from .object import ObjectObserver, Object

log = logging.getLogger(__name__)


FETCH_ELEMENT_COUNT = 200  # how many rows to re-request when all fetched elements are filtered out


@total_ordering
class Element(object):

    @classmethod
    def from_data(cls, iface, rec):
        key = getattr(rec.row, iface.get_key_column_id())
        return cls(key, rec.row, [Command(id) for id in rec.commands])

    def __init__(self, key, row, commands=None, order_key=None):
        assert is_list_inst(commands or [], Command), repr(commands)
        self.key = key
        self.row = row
        self.commands = commands or []
        self.order_key = order_key  # may be None

    def __repr__(self):
        return '<Element #%r order_key=%r %r>' % (self.key, self.order_key, self.row)

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        return iface.Element(self.row, [cmd.id for cmd in self.commands])

    def __eq__(self, other):
        if isinstance(other, Element):
            return self.key == other.key
        else:
            return self.key == other

    def __lt__(self, other):
        if isinstance(other, Element):
            return (self.order_key, self.key) < (other.order_key, other.key)
        else:
            return (self.order_key < other)

    def clone_with_sort_column(self, sort_column_id):
        order_key = getattr(self.row, sort_column_id)
        return Element(self.key, self.row, self.commands, order_key)


class Chunk(object):

    def __init__(self, sort_column_id, from_key, elements, bof, eof):
        assert isinstance(sort_column_id, str), repr(sort_column_id)
        assert is_list_inst(elements, Element), repr(elements)
        self.sort_column_id = sort_column_id
        self.from_key = from_key
        self.elements = elements
        self.bof = bof
        self.eof = eof

    def __eq__(self, other):
        if not isinstance(other, Chunk):
            return False
        return (self.sort_column_id == other.sort_column_id
                and self.from_key == other.from_key
                and self.elements == other.elements
                and self.bof == other.bof
                and self.eof == other.eof)

    def __repr__(self):
        return ('Chunk(sort_column_id=%r from_key=%r bof=%r eof=%r %d elements %s)'
                % (self.sort_column_id, self.from_key, self.bof, self.eof, len(self.elements),
                   '%r-%r' % (self.elements[0].key, self.elements[-1].key) if self.elements else ''))

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        elements = [elt.to_data(iface) for elt in self.elements]
        return iface.Chunk(self.sort_column_id, self.from_key, elements, self.bof, self.eof)

    def clone(self, from_key=None, elements=None, bof=None):
        if from_key is None:
            from_key = self.from_key
        if elements is None:
            elements = self.elements
        if bof is None:
            bof = self.bof
        return Chunk(self.sort_column_id, from_key, elements, bof, self.eof)


class ListDiff(Diff):

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

    def process_fetch_result(self, result):
        pass

    def diff_applied(self, diff):
        pass


class ListObject(Object, metaclass=abc.ABCMeta):

    def __init__(self):
        super().__init__()
        self._filter = None  # function: row -> bool

    # return list_interface.Column list
    @abc.abstractmethod
    def get_columns(self):
        pass

    @abc.abstractmethod
    def get_key_column_id(self):
        pass

    def set_filter(self, filter):
        self._filter = filter

    @abc.abstractmethod
    async def fetch_elements_impl(self, sort_column_id, key, desc_count, asc_count):
        pass

    async def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        original_from_key = key
        bof = None
        while True:
            list_chunk = await self.fetch_elements_impl(sort_column_id, key, desc_count, asc_count)
            assert isinstance(list_chunk, Chunk), (
                '%s.fetch_result_impl returned %r but expected is common.list_object.Chunk' % (self.__class__.__name__, list_chunk))
            if not list_chunk.elements:
                assert list_chunk.eof  # at least one element must be returned if eof not reached
            if not self._filter:
                break  # cycling is for filter only
            if bof is None:
                # this is first fetch_elements_impl call, save it's bof for returning to caller
                bof = list_chunk.bof
            if not list_chunk.elements:
                list_chunk = list_chunk.clone(from_key=original_from_key, bof=bof)
                break
            desc_count = 0
            key = list_chunk.elements[-1].key
            filtered_elements = list(filter(lambda element: self._filter(element.row), list_chunk.elements))
            list_chunk = list_chunk.clone(from_key=original_from_key, elements=filtered_elements, bof=bof)
            if list_chunk.elements:
                break
            log.info('   > list_object: all elements are filtered out, requesting more')
        self._notify_fetch_result(list_chunk)
        return list_chunk

    async def fetch_element(self, key):
        sort_column_id = self.get_key_column_id()
        chunk = await self.fetch_elements(sort_column_id, key, 1, 1)
        matched_elements = [element for element in chunk.elements if element.key == key]
        assert matched_elements, repr(matched_elements)  # at least one element with this key is expected
        return matched_elements[0]

    def get_element_command_list(self, element_key):
        return self.get_command_list(kinds=['element'])  # by default all elements have same commands

    # currently unused
    async def run_element_command(self, command_id, element_key):
        return (await self.run_command(command_id, element_key=element_key))

    def _notify_fetch_result(self, chunk):
        assert isinstance(chunk, Chunk), repr(chunk)
        for observer in self._observers:
            log.debug('  Calling process_fetch_result on %s/%s', id(observer), observer)
            observer.process_fetch_result(chunk)

    def _notify_diff_applied(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)

    def __del__(self):
        log.debug('~list_object self=%s', id(self))
