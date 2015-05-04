from PySide import QtCore, QtGui
from util import dt2local_str
from object import Object


class ColumnType(object):

    def to_string( self, value ):
        raise NotImplementedError(self.__class__)


class StrColumnType(ColumnType):

    def to_string( self, value ):
        return value


class DateTimeColumnType(ColumnType):

    def to_string( self, value ):
        return dt2local_str(value)


class Column(object):

    def __init__( self, idx, id, title, type ):
        self.idx = idx
        self.id = id
        self.title = title
        self.type = type


class Element(object):

    def __init__( self, key, row, commands ):
        self.key = key
        self.row = row
        self.commands = commands


class ListDiff(object):

    @classmethod
    def add_many( cls, key, elements ):
        return cls(key, key, elements)

    @classmethod
    def append_many( cls, key, elements ):
        return cls.add_many(None, elements)

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (but not including) this one
        self.elements = elements    # with these elemenents


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def element_count( self ):
        raise NotImplementedError(self.__class__)

    def need_elements_count( self, elements_count, force_load ):
        raise NotImplementedError(self.__class__)

    @staticmethod
    def _find_key_column( columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'

    def run_element_command( self, initiator_view, command_id, element_key ):
        raise NotImplementedError(self.__class__)

    def _notify_diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)
