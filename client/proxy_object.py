# Rationale for using __new__ to resolve  proxies from registry:
# I need to keep single proxy object per path for subscription/notification to work.
# This must work even when unpickling objects. Another solution for pickling/unpickling could be
# persistent_id/persistend_load mechanism, but in that case class and state information
# stored in pickle would be lost. I would need to construct proxy objects by myself then if unpickled
# instance is first with this 'path'.

import weakref
import uuid
from common.interface import Interface, Field, TRecord, TString, TPath, resolve_iface
from common.request import StrColumnType, DateTimeColumnType, Column, Element, ListDiff, ClientNotification, Request
from object import Object
from list_object import ListObject
from command import ObjectCommand, ElementCommand
import proxy_registry
import view


class RespHandler(proxy_registry.RespHandler):

    def __init__( self, object, command_id, initiator_view ):
        assert isinstance(object, Object), repr(object)
        proxy_registry.RespHandler.__init__(self, object.iface, command_id)
        assert initiator_view is None or isinstance(initiator_view, view.View), repr(initiator_view)
        self.object = weakref.ref(object)
        self.initiator_view = weakref.ref(initiator_view) if initiator_view else None  # may be initiated not by a view

    def process_response( self, response ):
        object = self.object()
        initiator_view = self.initiator_view() if self.initiator_view else None
        if object:
            object.process_response(response, self, self.command_id, initiator_view)



class ProxyObject(Object):

    @classmethod
    def from_response( cls, server, path, iface, contents ):
        object = cls(server, path, iface)
        object.set_contents(contents)
        return object

    # this schema allows resolving/deduplicating objects while unpickling
    def __new__( cls, server, path, *args, **kw ):
        obj = proxy_registry.resolve_proxy(path)
        if obj:
            return obj
        else:
            return object.__new__(cls, server, path, *args, **kw)

    def __init__( self, server, path, iface ):
        if hasattr(self, 'init_flag'): return   # after __new__ returns resolved object __init__ is called anyway
        Object.__init__(self)
        self.init_flag = None
        self.server = server
        self.path = path
        self.iface = iface
        self.commands = []
        self.resp_handlers = set()  # explicit refs to ObjectRespHandler to keep them alive until object is alive
        proxy_registry.register_proxy(self.path, self)

    def __getnewargs__( self ):
        return (self.server, self.path)

    def __getstate__( self ):
        state = Object.__getstate__(self)
        del state['resp_handlers']
        del state['iface']
        state['iface_id'] = self.iface.iface_id
        return state

    def __setstate__( self, state ):
        if hasattr(self, 'init_flag'): return  # after __new__ returns resolved object __setstate__ is called anyway too
        Object.__setstate__(self, state)
        self.iface = resolve_iface(state['iface_id'])
        self.resp_handlers = set()
        proxy_registry.register_proxy(self.path, self)
        self.execute_request('subscribe')

    def set_contents( self, contents ):
        self.commands = [ObjectCommand.from_json(cmd) for cmd in contents.commands]

    def get_title( self ):
        return ','.join('%s=%s' % (key, value) for key, value in self.path.items())

    def get_commands( self ):
        return self.commands

    def run_command( self, command_id, initiator_view=None, **kw ):
        self.execute_request(command_id, initiator_view, **kw)

    def observers_gone( self ):
        self.send_notification('unsubscribe')

    # prepare request which does not require/expect response
    def prepare_notification( self, command_id, **kw ):
        return ClientNotification(self.iface, self.path, command_id, params=kw)

    def prepare_request( self, command_id, **kw ):
        self.iface.validate_request(command_id, kw)
        request_id = str(uuid.uuid4())
        return Request(self.server, self.iface, self.path, command_id, request_id, params=kw)

    def send_notification( self, command_id, **kw ):
        request = self.prepare_notification(command_id, **kw)
        self.server.send_notification(request)

    def execute_request( self, command_id, initiator_view=None, **kw ):
        request = self.prepare_request(command_id, **kw)
        resp_handler = RespHandler(self, command_id, initiator_view)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def process_response( self, response, resp_handler, command_id, initiator_view ):
        result = response.result
        self.process_response_result(command_id, result)
        self.resp_handlers.remove(resp_handler)
        if not self.iface.is_open_command(command_id): return
        if result is None: return  # no new view opening is requested
        assert isinstance(result, view.Handle), repr(result)
        if not initiator_view: return  # view may already be gone (closed, navigated away) or be missing at all
        initiator_view.open(result)

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
        self.columns = []
        self.key_column_idx = None
        self.elements = []
        self.all_elements_fetched = False
        self.fetch_pending = False  # has pending element fetch request

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self.columns = contents.columns
        self.key_column_idx = self._find_key_column(self.columns)
        self.elements = contents.elements
        self.all_elements_fetched = not contents.has_more

    def process_update( self, diff ):
        print 'process_update', self, diff, diff.start_key, diff.end_key, diff.elements
        if self.elements and self.elements[0].key < self.elements[-1].key:  # ascending keys
            assert diff.start_key <= diff.end_key, (diff.start_key, diff.end_key)
            self.elements = \
              [elt for elt in self.elements if elt.key < diff.start_key] \
              + diff.elements \
              + [elt for elt in self.elements if elt.key > diff.end_key]
        else:  # descending keys or single element (todo)
            assert diff.start_key >= diff.end_key, (diff.start_key, diff.end_key)
            self.elements = \
              [elt for elt in self.elements if elt.key > diff.start_key] \
              + diff.elements \
              + [elt for elt in self.elements if elt.key < diff.end_key]
        self._notify_diff_applied(diff)

    def get_columns( self ):
        return self.columns

    def element_count( self ):
        return len(self.elements)

    def get_fetched_elements( self ):
        return self.elements

    def need_elements_count( self, elements_count, force_load ):
        if self.all_elements_fetched: return
        if self.fetch_pending: return
        if len(self.elements) >= elements_count and not force_load: return
        if self.elements:
            last_key = self.elements[-1].key
        else:
            last_key = None
        request_count = max(0, elements_count - len(self.elements))  # may be 0 in case of force_load, it is ok
        self.execute_request('get_elements', key=last_key, count=request_count)
        self.fetch_pending = True

    def process_response_result( self, command_id, result ):
        if command_id == 'get_elements':
            self.process_get_elements_result(result)
        ProxyObject.process_response_result(self, command_id, result)

    def process_get_elements_result( self, result ):
        self.fetch_pending = False
        result_elts = result.fetched_elements
        new_elements = [self.element_from_json(elt) for elt in result_elts.elements]
        self.elements += new_elements
        self.all_elements_fetched = not result_elts.has_more
        self._notify_diff_applied(ListDiff(None, None, new_elements))

    def __del__( self ):
        print '~ProxyListObject', self, self.path


proxy_registry.register_iface('list', ProxyListObject.from_response)
