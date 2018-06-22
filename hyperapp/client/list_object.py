import logging
import abc
import asyncio
from PySide import QtCore, QtGui

from ..common.util import is_list_inst, dt2local_str
from ..common.htypes import Type, tString
from ..common.list_object import Element, Chunk, ListDiff
from .object import ObjectObserver, Object

log = logging.getLogger(__name__)


FETCH_ELEMENT_COUNT = 200  # how many rows to re-request when all fetched elements are filtered out


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
            observer.process_fetch_result(chunk)

    def _notify_diff_applied(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)

    def __del__(self):
        log.debug('~list_object self=%s', id(self))
