from ..list_object import Element, Slice, ListObject


class IdentityList(ListObject):

    def __init__( self ):
        ListObject.__init__(self)

    def get_title( self ):
        return 'Identity list'

    def get_commands( self ):
        return []

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        return Slice('name', None, 'asc', [], bof=True, eof=True)
