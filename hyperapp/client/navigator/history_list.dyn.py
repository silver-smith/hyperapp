import logging
from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import tInt
from hyperapp.client.command import command
from . import htypes
from .column import Column
from .list_object import ListObject

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
    def command_open(self, item_key):
        return self._history[item_key].handle

    def get_columns(self):
        return [
            Column('idx', type=tInt, is_key=True),
            Column('title'),
            ]

    async def fetch_items(self, from_key):
        self._distribute_fetch_results(
            [self._Row(idx, item.title) for idx, item in enumerate(self._history)])
        self._distribute_eof()
