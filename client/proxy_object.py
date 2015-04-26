# Rationale for using __new__ to resolve  proxies from registry:
# I need to keep single proxy object per path for subscription/notification to work.
# This must work even when unpickling objects. Another solution for pickling/unpickling could be
# persistent_id/persistend_load mechanism, but in that case class and state information
# stored in pickle would be lost. I would need to construct proxy objects by myself then if unpickled
# instance is first with this 'path'.

import weakref
import uuid
from object import Object
from list_object import StrColumnType, DateTimeColumnType, Column, Element, ListDiff, ListObject
from command import ObjectCommand, ElementCommand
import proxy_registry


class ObjectRespHandler(proxy_registry.RespHandler):

    def __init__( self, object, initiator_view, requested_method ):
        self.object = weakref.ref(object)
        self.initiator_view = weakref.ref(initiator_view) if initiator_view else None  # may be initiated not by a view
        self.requested_method = requested_method

    def process_response( self, response ):
        object = self.object()
        initiator_view = self.initiator_view() if self.initiator_view else None
        if object:
            object.process_response(self, initiator_view, self.requested_method, response)


class ProxyObject(Object):

    # this schema allows resolving/deduplicating objects while unpickling
    def __new__( cls, server, path, *args, **kw ):
        obj = proxy_registry.resolve_proxy(path)
        if obj:
            return obj
        else:
            return object.__new__(cls)

    def __init__( self, server, path, commands ):
        if hasattr(self, 'init_flag'): return   # after __new__ returns resolved object __init__ is called anyway
        Object.__init__(self)
        self.init_flag = None
        self.server = server
        self.path = path
        self.commands = commands
        self.resp_handlers = set()  # explicit refs to ObjectRespHandler to keep them alive until object is alive
        proxy_registry.register_proxy(self.path, self)

    def __getnewargs__( self ):
        return (self.server, self.path)

    def __setstate__( self, state ):
        if hasattr(self, 'init_flag'): return  # after __new__ returns resolved object __setstate__ is called anyway too
        Object.__setstate__(self, state)
        proxy_registry.register_proxy(self.path, self)

    @staticmethod
    def parse_resp( resp ):
        path = resp['path']
        commands = [ObjectCommand.from_json(cmd) for cmd in resp['commands']]
        return (path, commands)

    def get_title( self ):
        return ','.join('%s=%s' % (key, value) for key, value in self.path.items())

    def get_commands( self ):
        return self.commands

    def prepare_request( self, method, **kw ):
        request_id = str(uuid.uuid4())
        request = dict(
            method=method,
            path=self.path,
            request_id=request_id,
            **kw)
        return request

    def prepare_command_request( self, command_id, **kw ):
        return self.prepare_request('run_command', command_id=command_id, **kw)

    def execute_request( self, initiator_view, request ):
        resp_handler = ObjectRespHandler(self, initiator_view, request['method'])
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def run_command( self, initiator_view, command_id, **kw ):
        request = self.prepare_command_request(command_id, **kw)
        self.execute_request(initiator_view, request)

    def process_response( self, resp_handler, initiator_view, request_method, response ):
        self.resp_handlers.remove(resp_handler)
        self.process_response_result(request_method, response.result)
        handle = response.get_handle2open()
        if not handle: return  # is new view opening is requested?
        if not initiator_view: return  # view may already be gone (closed, navigated away) or be missing at all
        initiator_view.open(handle)

    def process_response_result( self, request_method, result ):
        pass

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)

    def __del__( self ):
        print '~ProxyObject', self, self.path


class ProxyListObject(ProxyObject, ListObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        columns = [cls.column_from_json(idx, column) for idx, column in enumerate(resp['columns'])]
        key_column_idx = cls._find_key_column(columns)
        elements = [cls.element_from_json(elt) for elt in resp['elements']]
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
    def element_from_json( data ):
        key = data['key']
        row = data['row']
        return Element(key, row, [ElementCommand.from_json(cmd) for cmd in data['commands']])

    @classmethod
    def list_diff_from_json( cls, data ):
        return ListDiff(
            start_key=data['start_key'],
            end_key=data['end_key'],
            elements=[cls.element_from_json(elt) for elt in data['elements']],
            )


    def __init__( self, server, path, commands, columns, elements, all_elements_fetched, key_column_idx ):
        ProxyObject.__init__(self, server, path, commands)
        ListObject.__init__(self)
        self.columns = columns
        self.elements = elements
        self.all_elements_fetched = all_elements_fetched
        self.key_column_idx = key_column_idx
        self.fetch_pending = False  # has pending element fetch request

    def process_update( self, diff ):
        print 'process_update', self, diff, diff.start_key, diff.end_key, diff.elements
        self.elements = \
          [elt for elt in self.elements if elt.key < diff.start_key] \
          + diff.elements \
          + [elt for elt in self.elements if elt.key >= diff.end_key]
        self._notify_object_changed()

    def get_columns( self ):
        return self.columns

    def element_count( self ):
        return len(self.elements)

    def get_fetched_elements( self ):
        return self.elements

    def need_elements_count( self, elements_count ):
        if self.all_elements_fetched: return
        if len(self.elements) >= elements_count: return
        if self.fetch_pending: return
        if self.elements:
            last_key = self.elements[-1].key
        else:
            last_key = None
        request_count = elements_count - len(self.elements)
        request = self.prepare_request('get_elements', key=last_key, count=request_count)
        self.execute_request(None, request)
        self.fetch_pending = True

    def process_response_result( self, request_method, result ):
        if request_method == 'get_elements':
            self.process_get_elements_result(result)

    def process_get_elements_result( self, result ):
        self.fetch_pending = False
        result_elts = result.fetched_elements
        new_elements = [self.element_from_json(elt) for elt in result_elts['elements']]
        self.elements += new_elements
        self.all_elements_fetched = not result_elts['has_more']
        self._notify_diff_applied(ListDiff(None, None, new_elements))
        
    def run_element_command( self, initiator_view, command_id, element_key ):
        request = self.prepare_request('run_element_command', command_id=command_id, element_key=element_key)
        self.execute_request(initiator_view, request)

    def __del__( self ):
        print '~ProxyListObject', self, self.path


proxy_registry.register_iface('list', ProxyListObject.from_resp)
