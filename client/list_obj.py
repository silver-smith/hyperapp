from PySide import QtCore, QtGui
from util import dt2local_str
from command import ObjectCommand, ElementCommand
from proxy_object import ProxyObject
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

    def __init__( self, key, row, commands ):
        self.key = key
        self.row = row
        self.commands = commands

    @classmethod
    def from_json( cls, key_column_idx, data ):
        row = data['row']
        key = row[key_column_idx]
        return cls(key, row, [ElementCommand.from_json(cmd) for cmd in data['commands']])


class ListObj(ProxyObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        columns = [Column.from_json(idx, column) for idx, column in enumerate(resp['columns'])]
        key_column_idx = cls._find_key_column(columns)
        elements = [Element.from_json(key_column_idx, elt) for elt in resp['elements']]
        all_elements_fetched = not resp['has_more']
        return cls(server, path, commands, columns, elements, all_elements_fetched, key_column_idx)

    def __init__( self, server, path, commands, columns, elements, all_elements_fetched, key_column_idx ):
        ProxyObject.__init__(self, server, path, commands)
        self.columns = columns
        self.elements = elements
        self.all_elements_fetched = all_elements_fetched
        self.key_column_idx = key_column_idx

    def get_columns( self ):
        return self.columns

    def element_count( self ):
        return len(self.elements)

    def get_elements( self ):
        return self.elements

    def are_all_elements_fetched( self ):
        return self.all_elements_fetched

    def load_elements( self, load_count ):
        if self.elements:
            last_key = self.elements[-1].key
        else:
            last_key = None
        request = dict(
            method='get_elements',
            path=self.path,
            key=last_key,
            count=load_count)
        response = self.server.execute_request(request)
        result_elts = response.result.fetched_elements
        self.elements += [Element.from_json(self.key_column_idx, elt) for elt in result_elts['elements']]
        self.all_elements_fetched = not result_elts['has_more']

    @staticmethod
    def _find_key_column( columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'

    def run_element_command( self, command_id, element_key ):
        request = dict(
            method='run_element_command',
            path=self.path,
            command_id=command_id,
            element_key=element_key,
            )
        return self.server.request_an_object(request)


iface_registry.register_iface('list', ListObj.from_resp)
