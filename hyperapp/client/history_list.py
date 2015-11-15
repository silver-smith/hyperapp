from ..common.util import is_list_inst
from ..common.interface import intColumnType, Column
from .pickler import pickler
from .command import ElementCommand
from .list_object import Element, Slice, ListObject


class PickledHandle(object):

    @classmethod
    def from_handle( cls, handle ):
        return cls(pickler.dumps(handle))

    def __init__( self, pickled_handle ):
        self.pickled_handle = pickled_handle

    def load( self ):
        handle = pickler.loads(self.pickled_handle)
        object = handle.get_object()
        if object:
            object.server_subscribe()
        return handle


class HistoryRow(object):

    def __init__( self, idx, title, pickled_handle ):
        assert isinstance(pickled_handle, PickledHandle), repr(pickled_handle)
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
        handle = self._rows[element_key].pickled_handle.load()
        initiator_view.open(handle)

    def get_columns( self ):
        return [
            Column('idx', type=intColumnType),
            Column('title', 'Title'),
            ]

    def get_key_column_id( self ):
        return 'idx'

    def get_default_sort_column_id( self ):
        return 'idx'

    def subscribe_and_fetch_elements( self, observer, sort_column_id, key, desc_count, asc_count ):
        self.subscribe(observer)
        self.fetch_elements(sort_column_id, key, desc_count, asc_count)

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        return Slice('idx', None, 'asc', map(self._row2element, self._rows), bof=True, eof=True)

    def _row2element( self, row ):
        commands = [ElementCommand('open', 'Open', 'Open selected item')]
        return Element(row.idx, row, commands)
