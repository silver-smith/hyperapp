import asyncio
from ..common.util import is_list_inst
from ..common.htypes import intColumnType, Column, tHandle
from .command import ElementCommand
from .list_object import Element, Slice, ListObject


class HistoryRow(object):

    def __init__( self, idx, item ):
        self.idx = idx
        self.title = item.title
        self.item = item


class HistoryList(ListObject):

    def __init__( self, rows ):
        assert is_list_inst(rows, HistoryRow), repr(rows)
        ListObject.__init__(self)
        self._rows = rows

    def get_title( self ):
        return 'Navigation history'

    def get_commands( self ):
        return []

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        if command_id == 'open':
            return self.run_command_open(**kw)
        return (yield from ListObject.run_command(self, command_id, **kw))

    def run_command_open( self, element_key ):
        return self._rows[element_key].item.load()

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
        return Slice('idx', None, 'asc', list(map(self._row2element, self._rows)), bof=True, eof=True)

    def _row2element( self, row ):
        commands = [ElementCommand('open', 'Open', 'Open selected item')]
        return Element(row.idx, row, commands)
