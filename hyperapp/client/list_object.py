import logging
import abc
from PySide import QtCore, QtGui
from ..common.util import is_list_inst, dt2local_str
from ..common.htypes import ListInterface
from ..common.list_object import Element, Chunk, ListDiff
from .object import ObjectObserver, Object

log = logging.getLogger(__name__)


class ListObserver(ObjectObserver):

    def process_fetch_result(self, result):
        pass

    def diff_applied(self, diff):
        pass


class ListObject(Object, metaclass=abc.ABCMeta):

    # return list_interface.Column list
    @abc.abstractmethod
    def get_columns(self):
        pass

    @abc.abstractmethod
    def get_key_column_id(self):
        pass

    @abc.abstractmethod
    async def fetch_elements_impl(self, sort_column_id, key, desc_count, asc_count):
        pass

    async def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        list_chunk = await self.fetch_elements_impl(sort_column_id, key, desc_count, asc_count)
        assert isinstance(list_chunk, Chunk), '%s.fetch_result_impl returned %r but expected is common.list_object.Chunk' % (self.__class__.__name__, list_chunk)
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
