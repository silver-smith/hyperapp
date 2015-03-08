import weakref
from util import path2str
from object import Object
from list_object import StrColumnType, DateTimeColumnType, Column, Element, ListObject
from command import ObjectCommand, ElementCommand
import iface_registry


class ProxyObject(Object):

    # we want only one object per path, otherwise subscription/notification won't work
    proxy_registry = weakref.WeakValueDictionary()  # path -> ProxyObject

    # this schema allows resolving objects while unpickling
    def __new__( cls, server, path, *args, **kw ):
        obj = cls.resolve_proxy(path)
        if obj:
            print '> resolved from registry:', path, obj
            return obj
        return object.__new__(cls)

    @classmethod
    def resolve_proxy( cls, path ):
        print '  resolve_proxy:', path2str(path), cls.proxy_registry.get(path2str(path))
        return cls.proxy_registry.get(path2str(path))

    def __init__( self, server, path, commands ):
        Object.__init__(self)
        self.server = server
        self.path = path
        self.commands = commands
        self.register_proxy()

    def register_proxy( self ):
        path_str = path2str(self.path)
        if path_str not in self.proxy_registry:
            self.proxy_registry[path_str] = self
            print '< registered in registry:', self.path, self

    @staticmethod
    def parse_resp( resp ):
        path = resp['path']
        commands = [ObjectCommand.from_json(cmd) for cmd in resp['commands']]
        return (path, commands)

    def get_title( self ):
        return ','.join('%s=%s' % (key, value) for key, value in self.path.items())

    def get_commands( self ):
        return self.commands

    def make_command_request( self, command_id ):
        return dict(
            method='run_command',
            path=self.path,
            command_id=command_id,
            )

    def run_command( self, command_id ):
        request = self.make_command_request(command_id)
        return self.server.request_an_object(request)


class ProxyListObject(ProxyObject, ListObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        columns = [cls.column_from_json(idx, column) for idx, column in enumerate(resp['columns'])]
        key_column_idx = cls._find_key_column(columns)
        elements = [cls.element_from_json(key_column_idx, elt) for elt in resp['elements']]
        all_elements_fetched = not resp['has_more']
        return cls(server, path, commands, columns, elements, all_elements_fetched, key_column_idx)

    @staticmethod
    def column_from_json( idx, data ):
        ts = data['type']
        if ts == 'str':
            t = StrColumnType()
        elif ts == 'datetime':
            t = DateTimeColumnType()
        else:
            assert False, repr(t)  # Unknown column type
        return Column(idx, data['id'], data['title'], t)

    @staticmethod
    def element_from_json( key_column_idx, data ):
        row = data['row']
        key = row[key_column_idx]
        return Element(key, row, [ElementCommand.from_json(cmd) for cmd in data['commands']])


    def __init__( self, server, path, commands, columns, elements, all_elements_fetched, key_column_idx ):
        ProxyObject.__init__(self, server, path, commands)
        ListObject.__init__(self)
        self.columns = columns
        self.elements = elements
        self.all_elements_fetched = all_elements_fetched
        self.key_column_idx = key_column_idx

    def get_columns( self ):
        return self.columns

    def element_count( self ):
        return len(self.elements)

    def get_fetched_elements( self ):
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
        self.elements += [self.element_from_json(self.key_column_idx, elt) for elt in result_elts['elements']]
        self.all_elements_fetched = not result_elts['has_more']

    def run_element_command( self, command_id, element_key ):
        request = dict(
            method='run_element_command',
            path=self.path,
            command_id=command_id,
            element_key=element_key,
            )
        return self.server.request_an_object(request)

    def __del__( self ):
        print '~ProxyListObject', self.path


iface_registry.register_iface('list', ProxyListObject.from_resp)
