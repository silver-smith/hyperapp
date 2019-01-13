import logging
from hyperapp.common.util import is_list_inst
#from hyperapp.common.htypes import tInt, Column
from hyperapp.client.command import command
from hyperapp.client.list_object import Element, Chunk, ListObject
from . import htypes

log = logging.getLogger(__name__)


class HistoryList(ListObject):

    class _Row(object):

        def __init__(self, idx, title):
            self.idx = idx
            self.title = title


    impl_id = 'history_list'

    @classmethod
    def from_state(cls, state):
        assert isinstance(state, htypes.navigator.history_list), repr(state)  # using same state as navigator
        return cls(state.history)

    def __init__(self, history):
        assert is_list_inst(history, htypes.navigator.item), repr(history)
        ListObject.__init__(self)
        self._history = history

    def get_state(self):
        return htypes.navigator.history_list(self.impl_id, self._history)

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

    async def fetch_elements_impl(self, sort_column_id, key, desc_count, asc_count):
        return Chunk('idx', None, list(map(self._item2element, enumerate(self._history))), bof=True, eof=True)

    def _item2element(self, idx_and_item):
        idx, item = idx_and_item
        commands = [self.command_open]
        return Element(idx, self._Row(idx, item.title), commands)
