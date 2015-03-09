# Rationale for using __new__ to resolve  proxies from registry:
# I need to keep single proxy object per path for subscription/notification to work.
# This must work even when unpickling objects. Another solution for pickling/unpickling could be
# persistent_id/persistend_load mechanism, but in that case class and state information
# stored in pickling would be lost. I would need to construct proxy objects by myself then if unpickled
# instance is first with this 'path'.

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
        return cls.proxy_registry.get(path2str(path))

    @classmethod
    def process_updates( cls, updates ):
        for path, diff in updates:
            obj = cls.resolve_proxy(path)
            if obj:
                obj.process_update(diff)


    def __init__( self, server, path, commands ):
        if hasattr(self, 'init_flag'): return   # after __new__ returns resolved object __init__ is called anyway
        Object.__init__(self)
        self.init_flag = None
        self.server = server
        self.path = path
        self.commands = commands
        self.register_proxy()

    def __getnewargs__( self ):
        return (self.server, self.path)

    def __setstate__( self, state ):
        if hasattr(self, 'init_flag'): return  # after __new__ returns resolved object __setstate__ is called anyway too
        Object.__setstate__(self, state)
        self.register_proxy()

    def register_proxy( self ):
        path_str = path2str(self.path)
        assert path_str not in self.proxy_registry, repr(self.path)
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

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)


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

    def process_update( self, diff ):
        print 'process_update', self, diff, diff.start_key, diff.end_key, diff.elements
        # todo: adding elements
        self.elements = [elt for elt in self.elements
                         if elt.key < diff.start_key or elt.key >= diff.end_key]
        self._notify_object_changed()

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
        print '~ProxyListObject', self, self.path


iface_registry.register_iface('list', ProxyListObject.from_resp)
