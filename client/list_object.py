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


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def element_count( self ):
        raise NotImplementedError(self.__class__)

    def get_fetched_elements( self ):
        raise NotImplementedError(self.__class__)

    def are_all_elements_fetched( self ):
        raise NotImplementedError(self.__class__)

    def load_elements( self, load_count ):
        raise NotImplementedError(self.__class__)

    @staticmethod
    def _find_key_column( columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'

    def run_element_command( self, command_id, element_key ):
        raise NotImplementedError(self.__class__)
