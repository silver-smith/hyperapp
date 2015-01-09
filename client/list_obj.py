from PySide import QtCore, QtGui
from util import dt2local_str
from command import ObjectCommand, ElementCommand
from iface import ObjectIface
import iface_registry


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

    @classmethod
    def from_json( cls, idx, data ):
        ts = data['type']
        if ts == 'str':
            t = StrColumnType()
        elif ts == 'datetime':
            t = DateTimeColumnType()
        else:
            assert False, repr(t)  # Unknown column type
        return cls(idx, data['id'], data['title'], t)


class Element(object):

    def __init__( self, row, commands ):
        self.row = row
        self.commands = commands

    @classmethod
    def from_json( cls, data ):
        return cls(data['row'], [ElementCommand.from_json(cmd) for cmd in data['commands']])


class ListObj(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.columns = [Column.from_json(idx, column) for idx, column in enumerate(response['columns'])]
        self.elements = [Element.from_json(elt) for elt in response['elements']]
        self.key_column_idx = self._find_key_column(self.columns)

    def element_count( self ):
        return len(self.elements)

    def ensure_element_count( self, element_count ):
        if element_count < self.element_count(): return
        self.load_elements(element_count - self.element_count())

    def element_idx2key( self, idx ):
        return self.elements[idx].row[self.key_column_idx]

    def element2key( self, elt ):
        return elt.row[self.key_column_idx]

    def load_elements( self, load_count ):
        if self.elements:
            last_key = self.element_idx2key(-1)
        else:
            last_key = None
        request = dict(
            method='get_elements',
            path=self.path,
            key=last_key,
            count=load_count)
        response = self.server.execute_request(request)
        self.elements += [Element.from_json(elt) for elt in response['elements']]

    def _find_key_column( self, columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'


iface_registry.register_iface('list', ListObj)
