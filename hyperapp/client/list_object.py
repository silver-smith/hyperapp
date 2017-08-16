import logging
import asyncio
import abc
from PySide import QtCore, QtGui
from ..common.util import is_list_inst, dt2local_str
from ..common.htypes import ListInterface
from ..common.list_object import Element, Slice, ListDiff
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

    @asyncio.coroutine
    @abc.abstractmethod
    def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        pass

    @asyncio.coroutine
    def fetch_element(self, key):
        sort_column_id = self.get_key_column_id()
        slice = yield from self.fetch_elements(sort_column_id, key, 1, 1)
        matched_elements = [element for element in slice.elements if element.key == key]
        assert matched_elements, repr(matched_elements)  # at least one element with this key is expected
        return matched_elements[0]

    # currently unused
    @asyncio.coroutine
    def run_element_command(self, command_id, element_key):
        return (yield from self.run_command(command_id, element_key=element_key))

    def _notify_fetch_result(self, slice):
        assert isinstance(slice, Slice), repr(slice)
        for observer in self._observers:
            observer.process_fetch_result(slice)

    def _notify_diff_applied(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)

    def __del__(self):
        log.debug('~list_object self=%s', id(self))
