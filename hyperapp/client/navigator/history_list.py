import logging
import asyncio
from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import tInt, Column
from ..command import command
from ..list_object import Element, Chunk, ListObject
from .module import get_this_module

log = logging.getLogger(__name__)


def register_object_implementations(registry, services):
    this_module = get_this_module()
    registry.register(HistoryList.objimpl_id, HistoryList.from_state, this_module)


class HistoryList(ListObject):

    class _Row(object):

        def __init__(self, idx, title):
            self.idx = idx
            self.title = title


    objimpl_id = 'history_list'

    @classmethod
    def from_state(cls, state, this_module):
        assert isinstance(state, this_module.history_list_type), repr(state)  # using same state as navigator
        return cls(state.history, this_module)

    def __init__(self, history, this_module):
        assert is_list_inst(history, this_module.item_type), repr(history)
        ListObject.__init__(self)
        self._this_module = this_module
        self._history = history

    def get_state(self):
        return self._this_module.history_list_type(self.objimpl_id, self._history)

    def get_title(self):
        return 'Navigation history'

    def get_commands(self):
        return []

    @command('open', kind='element')
    def command_open(self, element_key):
        return self._history[element_key].handle

    def get_columns(self):
        return [
            Column('idx', type=tInt, is_key=True),
            Column('title'),
            ]

    def get_key_column_id(self):
        return 'idx'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        self._notify_fetch_result(self._get_chunk())

    def _get_chunk(self):
        return Chunk('idx', None, list(map(self._item2element, enumerate(self._history))), bof=True, eof=True)

    def _item2element(self, idx_and_item):
        idx, item = idx_and_item
        commands = [self.command_open]
        return Element(idx, self._Row(idx, item.title), commands)
