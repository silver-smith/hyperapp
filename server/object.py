from operator import attrgetter
from common.util import path2str
from common.interface import (
    tString,
    Field,
    ObjHandle,
    iface_registry,
    )
import common.interface.interface as interface_module
import common.interface.list as list_module
from util import WeakValueMultiDict
from common.interface import Interface


MIN_ROWS_RETURNED = 10


class Subscription(object):

    def __init__( self ):
        self.path2client = WeakValueMultiDict()  # path -> client

    def add( self, path, client ):
        self.path2client.add(path2str(path), client)

    def remove( self, path, client ):
        self.path2client.remove(path2str(path), client)

    def distribute_update( self, iface, path, diff ):
        update = iface.Update(path, diff)
        for client in self.path2client.get(path2str(path)):
            client.send_update(update)


subscription = Subscription()


class Object(interface_module.Object):

    def __init__( self ):
        pass

    def get_path( self ):
        raise NotImplementedError(self.__class__)

    def get_commands( self ):
        return []

    def get( self ):
        return self.iface.Object(
            iface=self.iface,
            proxy_id=self.proxy_id,
            path=self.get_path(),
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
        self.subscribe(request)
        return request.make_response(self.get_handle())

    def process_request_subscribe( self, request ):
        self.subscribe(request)
        return request.make_response(self.get_contents())

    def subscribe( self, request ):
        subscription.add(self.get_path(), request.peer)

    def unsubscribe( self, request ):
        subscription.remove(self.get_path(), request.peer)


class ListObject(Object, list_module.ListObject):

    default_sort_by_column = 'key'

    def __init__( self ):
        Object.__init__(self)

    def get_contents( self, **kw ):
        elements, bof, eof = self.fetch_elements(sort_by_column=default_sort_by_column)
        return Object.get_contents(self,
            sorted_by_column=default_sort_by_column,
            elements=elements,
            bof=bof,
            eof=eof,
            **kw)

    def get_handle( self ):
        return self.ListHandle(self)

    def process_request( self, request ):
        if request.command_id == 'fetch_elements':
            params = request.params
            elements, bof, eof = self.fetch_elements(params.sort_by_column, params.key, params.desc_count, params.asc_count)
            return request.make_response_result(elements=elements, bof=bof,eof=eof)
        elif request.command_id == 'run_element_command':
            return self.run_element_command(request, request.command_id, request.params.element_key)
        else:
            return Object.process_request(self, request)

    # must return tuple (self.iface.Element list, bof:bool, eof:bool)
    def fetch_elements( self, sort_by_column, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, request, command_id, element_key ):
        assert False, repr(command_id)  # Unexpected command_id


class SmallListObject(ListObject):

    def fetch_elements( self, sort_by_column, key, desc_count, asc_count ):
        elt2sort_key = attrgetter('row.%s' % self.iface.key_column)
        sorted_elements = sorted(self.fetch_all_elements(), key=elt2sort_key)
        for idx, element in enumerate(sorted_elements):
            if elt2sort_key(element) >= key:
                break
        else:
            idx = len(sorted_elements)
        elements = sorted_elements[idx - desc_count : idx + asc_count]
        bof = idx - desc_count > 0
        eof = idx + asc_count >= len(sorted_elements)
        return (elements, bof, eof)

    # must return self.iface.Element list
    def fetch_all_elements( self ):
        raise NotImplementedError(self.__class__)
    
