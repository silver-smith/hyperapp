from common.util import is_list_inst
from common.interface import intColumnType, Column
from .pickler import pickler
from .command import Command
from .list_object import Element, Slice, ListObject


class HistoryRow(object):

    def __init__( self, idx, title, pickled_handle ):
        self.idx = idx
        self.title = title
        self.pickled_handle = pickled_handle


class HistoryList(ListObject):

    def __init__( self, rows ):
        assert is_list_inst(rows, HistoryRow), repr(rows)
        ListObject.__init__(self)
        self._rows = rows

    def get_title( self ):
        return 'Navigation history'

    def get_commands( self ):
        return []

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'open':
            return self.run_command_open(initiator_view, **kw)
        return ListObject.run_command(self, command_id, initiator_view, **kw)

    def run_command_open( self, initiator_view, element_key ):
        handle = pickler.loads(self._rows[element_key].pickled_handle)
        initiator_view.open(handle)

    def get_columns( self ):
        return [
            Column('idx', type=intColumnType),
            Column('title', 'Title'),
            ]

    def get_key_column_id( self ):
        return 'idx'

    def get_initial_slice( self ):
        return self._get_slice()

    def subscribe_and_fetch_elements( self, observer, sort_column_id, key, desc_count, asc_count ):
        self.subscribe(observer)
        self.fetch_elements(sort_column_id, key, desc_count, asc_count)

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        return Slice('idx', map(self._row2element, self._rows), bof=True, eof=True)

    def _row2element( self, row ):
        commands = [Command('open', 'Open', 'Open selected item')]
        return Element(row.idx, row, commands)
