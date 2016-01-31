from operator import attrgetter
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    tString,
    Field,
    ObjHandle,
    Interface,
    iface_registry,
    )
from .util import WeakValueMultiDict


MIN_ROWS_RETURNED = 100


class Subscription(object):

    def __init__( self ):
        self.path2client = WeakValueMultiDict()  # path -> client

    def add( self, path, client ):
        self.path2client.add(encode_path(path), client)

    def remove( self, path, client ):
        self.path2client.remove(encode_path(path), client)

    def distribute_update( self, iface, path, diff ):
        update = iface.Update(path, diff)
        for client in self.path2client.get(encode_path(path)):
            client.send_update(update)


subscription = Subscription()


class Object(object):

    def __init__( self ):
        pass

    def get_path( self ):
        raise NotImplementedError(self.__class__)

    def get_commands( self ):
        return []

    def get( self ):
        path = self.get_path()
        assert is_list_inst(path, basestring), '%s.get_path must return list of strings, but returned: %r' % (self.__class__.__name__, path)
        return self.iface.Object(
            objimpl_id=self.objimpl_id,
            iface=self.iface.iface_id,
            path=path,
            contents=self.get_contents(),
            )

    def get_contents( self, **kw ):
        return self.iface.Contents(
            commands=self.get_commands(),
            **kw)

    def get_handle( self ):
        raise NotImplementedError(self.__class__)

    def process_request( self, request ):
        command_id = request.command_id
        if command_id == 'get':
            return self.process_request_get(request)
        if command_id == 'subscribe':
            return self.process_request_subscribe(request)
        elif command_id == 'subscribe':
            self.subscribe(request)
        elif command_id == 'unsubscribe':
            self.unsubscribe(request)
        else:
            assert False, repr(command_id)  # Unknown command

    def process_request_get( self, request ):
        return request.make_response(self.get_handle())

    def process_request_subscribe( self, request ):
        self.subscribe(request)
        return request.make_response(self.get_contents())

    def subscribe( self, request ):
        subscription.add(self.get_path(), request.peer)

    def unsubscribe( self, request ):
        subscription.remove(self.get_path(), request.peer)


class ListObject(Object):

    default_sort_column_id = 'key'
    default_direction = 'asc'

    @classmethod
    def Row( cls, *args, **kw ):
        return cls.iface.Row(*args, **kw)

    @classmethod
    def Element( cls, *args, **kw ):
        return cls.iface.Element(*args, **kw)

    @classmethod
    def Diff( cls, *args, **kw ):
        return cls.iface.Diff(*args, **kw)

    @classmethod
    def Diff_replace( cls, key, element ):
        return cls.Diff(key, key, [element])

    @classmethod
    def Diff_insert_one( cls, key, element ):
        return cls.Diff_insert_many(key, [element])

    @classmethod
    def Diff_insert_many( cls, key, elements ):
        return cls.Diff(key, key, elements)

    @classmethod
    def Diff_append_many( cls, elements ):
        return cls.Diff.insert_many(None, elements)

    @classmethod
    def Diff_delete( cls, key ):
        return cls.Diff(key, key, [])

    @classmethod
    def ListHandle( cls, object, sort_column_id=None, key=None ):
        if sort_column_id is None:
            sort_column_id = cls.default_sort_column_id
        return cls.iface.ListHandle('list', object, sort_column_id, key)

    @classmethod
    def ListNarrowerHandle( cls, object, sort_column_id=None, key=None, narrow_field_id=None ):
        if sort_column_id is None:
            sort_column_id = cls.default_sort_column_id
        if narrow_field_id is None:
            narrow_field_id = sort_column_id
        return cls.iface.ListNarrowerHandle('list_narrower', object, sort_column_id, key, narrow_field_id)

    def __init__( self ):
        Object.__init__(self)

    def get_contents( self, **kw ):
        slice = self.fetch_elements(self.default_sort_column_id, None, self.default_direction, MIN_ROWS_RETURNED)
        self.iface.tSlice().validate('Slice', slice)  # invalid result from fetch_elements, use: return self.Slice(...)
        return Object.get_contents(self, slice=slice, **kw)

    def get_handle( self ):
        return self.ListHandle(self.get())

    def process_request( self, request ):
        if request.command_id == 'fetch_elements':
            return self.process_request_fetch_elements(request)
        if request.command_id == 'subscribe_and_fetch_elements':
            self.subscribe(request)
            return self.process_request_fetch_elements(request)
        elif request.command_id == 'run_element_command':
            return self.run_element_command(request, request.command_id, request.params.element_key)
        else:
            return Object.process_request(self, request)

    def process_request_fetch_elements( self, request ):
        params = request.params
        slice = self.fetch_elements(params.sort_column_id, params.from_key, params.direction, params.count)
        self.iface.tSlice().validate('Slice', slice)  # invalid result from fetch_elements, use: return self.Slice(...)
        return request.make_response(Object.get_contents(self, slice=slice))

    # must return Slice, construct using self.Slice(...)
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, request, command_id, element_key ):
        assert False, repr(command_id)  # Unexpected command_id

    def Slice( self, sort_column_id, from_key, direction, elements, bof, eof ):
        assert isinstance(sort_column_id, basestring), repr(sort_column_id)
        column = self._pick_column(sort_column_id)
        assert column, 'Unknown column: %r; known are: %r'\
           % (sort_column_id, [column.id for column in self.iface.columns])
        assert direction in ['asc', 'desc'], repr(direction)
        return self.iface.Slice(sort_column_id, from_key, direction, elements, bof, eof)
            
    def _pick_column( self, column_id ):
        for column in self.iface.columns:
            if column.id == column_id:
                return column
        return None


class SmallListObject(ListObject):

    def fetch_elements( self, sort_column_id, from_key, direction, count ):
        assert direction == 'asc', repr(direction)  # Descending direction is not yet supported
        elt2sort_key = attrgetter('row.%s' % self.iface.key_column)
        sorted_elements = sorted(self.fetch_all_elements(), key=elt2sort_key)
        if from_key is None:
            idx = 0
        else:
            for idx, element in enumerate(sorted_elements):
                if elt2sort_key(element) > from_key:
                    break
            else:
                idx = len(sorted_elements)
        if count < MIN_ROWS_RETURNED:
            count = MIN_ROWS_RETURNED
        elements = sorted_elements[idx : idx+count]
        bof = idx == 0
        eof = idx + count >= len(sorted_elements)
        return self.Slice(sort_column_id, from_key, direction, elements, bof, eof)

    # must return self.iface.Element list
    def fetch_all_elements( self ):
        raise NotImplementedError(self.__class__)
    
