import weakref
import uuid
import bisect
from common.util import path2str
from common.interface import Interface, Field, tString, tPath, resolve_iface
import common.interface as interface_module
from common.request import ClientNotification, Request
from .object import Object
from .command import Command
from .list_object import ListDiff, Element, Slice, ListObject
from .proxy_registry import RespHandler, proxy_registry
from . import view


class ObjRespHandler(RespHandler):

    def __init__( self, object, command_id, initiator_view ):
        assert isinstance(object, Object), repr(object)
        RespHandler.__init__(self, object.iface, command_id)
        assert initiator_view is None or isinstance(initiator_view, view.View), repr(initiator_view)
        self.object = weakref.ref(object)
        self.initiator_view = weakref.ref(initiator_view) if initiator_view else None  # may be initiated not by a view

    def process_response( self, server, response ):
        object = self.object()
        initiator_view = self.initiator_view() if self.initiator_view else None
        if object:
            object.process_response(server, response, self, self.command_id, initiator_view)


class ProxyObject(Object, interface_module.Object):

    def __init__( self, server, path, iface ):
        Object.__init__(self)
        interface_module.Object.__init__(self)
        self.init_flag = None
        self.server = server
        self.path = path
        self.iface = iface
        self.commands = []
        self.resp_handlers = set()  # explicit refs to ObjRespHandlers to keep them alive until object is alive

    def get_persistent_id( self ):
        return ' '.join([self.get_proxy_id(),
                         self.iface.iface_id,
                         self.server.get_locator(),
                         path2str(self.path)])

    @staticmethod
    def get_proxy_id():
        return 'object'

    def subscribe( self, observer ):
        this_is_first_observer = Object.subscribe(self, observer)
        if this_is_first_observer:
            self.execute_request('subscribe')

    def set_contents( self, contents ):
        self.commands = map(Command.decode, contents.commands)

    def get_title( self ):
        return '/' + '/'.join(self.path)

    def get_commands( self ):
        return self.commands

    def run_command( self, command_id, initiator_view=None, **kw ):
        self.execute_request(command_id, initiator_view, **kw)

    def observers_gone( self ):
        print '-- observers_gone', self
        self.send_notification('unsubscribe')

    # prepare request which does not require/expect response
    def prepare_notification( self, command_id, *args, **kw ):
        params = self.iface.make_params(command_id, *args, **kw)
        return ClientNotification(self.server, self.iface, self.path, command_id, params=params)

    def prepare_request( self, command_id, *args, **kw ):
        request_id = str(uuid.uuid4())
        params = self.iface.make_params(command_id, *args, **kw)
        return Request(self.server, self.iface, self.path, command_id, request_id, params=params)

    def send_notification( self, command_id, *args, **kw ):
        request = self.prepare_notification(command_id, *args, **kw)
        self.server.send_notification(request)

    def execute_request( self, command_id, initiator_view=None, *args, **kw ):
        request = self.prepare_request(command_id, *args, **kw)
        resp_handler = ObjRespHandler(self, command_id, initiator_view)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def process_response( self, server, response, resp_handler, command_id, initiator_view ):
        result = response.result
        self.process_response_result(command_id, result)
        self.resp_handlers.remove(resp_handler)
        # initiator_view may already be gone (closed, navigated away) or be missing at all - so is None
        if self.iface.is_open_command(command_id) and initiator_view:
            initiator_view.process_handle_open(server, result)

    def process_response_result( self, command_id, result ):
        if command_id == 'subscribe':
            self.process_subscribe_response(result)

    def process_subscribe_response( self, result ):
        self.set_contents(result)
        self._notify_object_changed()

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)

    def __del__( self ):
        print '~ProxyObject', self, self.path


class ProxyListObject(ProxyObject, ListObject):

    def __init__( self, server, path, iface ):
        ProxyObject.__init__(self, server, path, iface)
        ListObject.__init__(self)
        self._initial_slice = None
        self._slices = []  # all slices are stored in ascending order

    @staticmethod
    def get_proxy_id():
        return 'list'

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self._initial_slice = self._decode_slice(contents.slice)
        self._slices.append(self._initial_slice)

    # We can use initial slice only once, immediately after receiving object contents.
    # After that contents may change
    def get_initial_slice( self ):
        slice = self._initial_slice
        self._initial_slice = None
        return slice

    def _decode_slice( self, rec ):
        key_column_id = self.get_key_column_id()
        elements = [Element.decode(key_column_id, rec.sort_column_id, elt_rec) for elt_rec in rec.elements]
        return Slice(rec.sort_column_id, rec.from_key, rec.direction, elements, rec.bof, rec.eof)

    def _merge_in_slice( self, new_slice ):
        print '  -- merge_in_slice', id(self), repr(new_slice.from_key), len(new_slice.elements), new_slice.bof, repr(new_slice.elements[0].key), repr(new_slice.elements[-1].key)
        assert new_slice.elements
        for slice in self._slices:
            if slice.sort_column_id != new_slice.sort_column_id: continue
            assert new_slice.direction == 'asc'  # todo: desc direction
            if new_slice.from_key == slice.elements[-1].key:
                assert not new_slice.bof  # this is continuation for existing slice, bof is not possible
                slice.elements.extend(new_slice.elements)
                slice.eof = new_slice.eof
                print '     > merged', len(slice.elements), repr(slice.elements[0].key), repr(slice.elements[-1].key)
                break
        else:
            self._slices.append(new_slice)
            print '     > added'

    def _pick_slice( self, sort_column_id, from_key, direction ):
        print '  -- pick_slice', id(self), repr(sort_column_id), repr(from_key), direction
        assert direction == 'asc'  # todo: desc direction
        for slice in self._slices:
            if slice.sort_column_id != sort_column_id: continue
            if from_key == None and slice.bof:
                print '     > bof found', len(slice.elements)
                return slice
            print '       - checking', len(slice.elements), repr(slice.elements[0].order_key), repr(slice.elements[-1].order_key)
            # here we assume sort_column_id == key_column_id:
            if slice.elements[0].order_key <= from_key and from_key <= slice.elements[-1].order_key:
                idx = bisect.bisect_left(slice.elements, from_key)  # must be from_order_key
                print '     - bisecting', idx
                while slice.elements[idx].order_key <= from_key:  # from_order_key
                    idx += 1
                    if slice.elements[idx-1].key == from_key: break  # from_order_key
                print '     - exact key', idx
                if idx < len(slice.elements):
                    print '     > middle found', idx, len(slice.elements), len(slice.elements[idx:])
                    return slice.clone_with_elements(slice.elements[idx:])
        print '     > none found'
        return None  # none found
            
    def subscribe_and_fetch_elements( self, observer, sort_column_id, from_key, direction, count ):
        this_is_first_observer = self.subscribe_local(observer)
        print '-- proxy subscribe_and_fetch_elements', this_is_first_observer, self, observer
        if not this_is_first_observer:
            return False
        slice = self._pick_slice(sort_column_id, from_key, direction)
        if slice:
            print '   > cached', len(slice.elements)
            self._notify_fetch_result(slice)
        else:
            print '   > no cached, requesting'
            self.execute_request('subscribe_and_fetch_elements', None, sort_column_id, from_key, direction, count)
        return True

    def process_update( self, diff ):
        print 'process_update', self, diff, diff.start_key, diff.end_key, diff.elements
        key_column_id = self.get_key_column_id()
        self._notify_diff_applied(ListDiff.decode(key_column_id, diff))

    def get_columns( self ):
        return self.iface.columns

    def get_key_column_id( self ):
        return self.iface.key_column

    def fetch_elements( self, sort_column_id, from_key, direction, count ):
        print '-- proxy fetch_elements', self, repr(from_key), count
        slice = self._pick_slice(sort_column_id, from_key, direction)
        if slice:
            print '   > cached', len(slice.elements)
            self._notify_fetch_result(slice)
        else:
            print '   > no cached, requesting'
            self.execute_request('fetch_elements', None, sort_column_id, from_key, direction, count)

    def process_response_result( self, command_id, result ):
        if command_id == 'subscribe_and_fetch_elements':
            self.process_subscribe_and_fetch_elements_result(result)
        elif command_id == 'fetch_elements':
            self.process_fetch_elements_result(result)
        else:
            ProxyObject.process_response_result(self, command_id, result)

    def process_subscribe_and_fetch_elements_result( self, result ):
        print '-- proxy process_subscribe_and_fetch_elements_result', self, len(result.slice.elements)
        ProxyObject.set_contents(self, result)
        slice = self._decode_slice(result.slice)
        self._merge_in_slice(slice)
        self._notify_object_changed()
        self._notify_fetch_result(slice)

    def process_fetch_elements_result( self, result ):
        print '-- proxy process_fetch_elements_result', self, len(result.slice.elements)
        slice = self._decode_slice(result.slice)
        self._merge_in_slice(slice)
        self._notify_fetch_result(slice)

    def __del__( self ):
        print '~ProxyListObject', self, self.path


proxy_registry.register_class(ProxyObject)
proxy_registry.register_class(ProxyListObject)
