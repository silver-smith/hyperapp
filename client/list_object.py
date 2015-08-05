from PySide import QtCore, QtGui
from common.util import dt2local_str
from object import Object


class ListDiff(object):

    @classmethod
    def add_one( cls, key, element ):
        return cls(key, key, [element])

    @classmethod
    def add_many( cls, key, elements ):
        return cls(key, key, elements)

    @classmethod
    def append_many( cls, elements ):
        return cls.add_many(None, elements)

    @classmethod
    def delete( cls, key ):
        return cls(key, key, [])

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def get_key_column_id( self ):
        raise NotImplementedError(self.__class__)

    def fetch_elements( self, sort_by_column, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, command_id, element_key, initiator_view ):
        return self.run_command(command_id, initiator_view, element_key=element_key)

    def _notify_fetch_result( self, result ):
        #assert isinstance(diff, ListDiff), repr(diff)  # may also be interface update Record
        for observer in self._observers:
            observer.process_fetch_result(result)

    def _notify_diff_applied( self, diff ):
        #assert isinstance(diff, ListDiff), repr(diff)  # may also be interface update Record
        for observer in self._observers:
            observer.diff_applied(diff)
