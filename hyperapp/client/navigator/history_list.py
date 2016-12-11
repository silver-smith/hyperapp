import logging
import asyncio
from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import intColumnType, Column
from ..command import command
from ..list_object import Element, Slice, ListObject
from .htypes import item_type, history_list_type

log = logging.getLogger(__name__)


def register_object_implementations( registry, services ):
    registry.register(HistoryList.objimpl_id, HistoryList.from_state)


class HistoryList(ListObject):

    class _Row(object):

        def __init__( self, idx, title ):
            self.idx = idx
            self.title = title


    objimpl_id = 'history_list'

    @classmethod
    def from_state( cls, state ):
        assert isinstance(state, history_list_type), repr(state)  # using same state as navigator
        return cls(state.history)

    def __init__( self, history ):
        assert is_list_inst(history, item_type), repr(history)
        ListObject.__init__(self)
        self._history = history

    def get_state( self ):
        return history_list_type(self.objimpl_id, self._history)

    def get_title( self ):
        return 'Navigation history'

    def get_commands( self ):
        return []

    @command('open', is_default_command=True)
    def command_open( self, element_key ):
        return self._history[element_key].handle

    def get_columns( self ):
        return [
            Column('idx', type=intColumnType),
            Column('title', 'Title'),
            ]

    def get_key_column_id( self ):
        return 'idx'

    @asyncio.coroutine
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        return Slice('idx', None, 'asc', list(map(self._item2element, enumerate(self._history))), bof=True, eof=True)

    def _item2element( self, idx_and_item ):
        idx, item = idx_and_item
        commands = [self.command_open]
        return Element(idx, self._Row(idx, item.title), commands)
