import weakref
from ..common.util import is_list_inst
from ..common.endpoint import Endpoint, Url
from ..common.htypes import (
    Interface,
    TList,
    Field,
    tString,
    TRecord,
    tCommand,
    tObject,
    tThisProxyObject,
    tProxyObject,
    tThisProxyObjectWithContents,
    tHandle,
    tViewHandle,
    tRedirectHandle,
    tPath,
    tEndpoint,
    resolve_iface,
    iface_registry,
    )
from .object import Object
from .command import Command
from .proxy_registry import proxy_class_registry, proxy_registry
from .request import ClientNotification, Request
from .server import Server
from .cache_repository import cache_repository
from .view import View
from .proxy_object_data_mapper import ProxyObjectMapper
from .redirect_handle_resolver import RedirectHandleCollector, RedirectHandleMapper


class RequestForResult(Request):

    def __init__( self, object, command_id, params ):
        assert isinstance(object, Object), repr(object)
        Request.__init__(self, object.iface, object.path, command_id, params)
        self.object = weakref.ref(object)

    def process_response( self, server, response ):
        object = self.object()
        if not object:
            print 'Received response #%s for a missing (already destroyed) object, ignoring' % response.request_id
            return
        object.process_response_result(self.command_id, response.result)


class OpenRequest(Request):

    def __init__( self, iface, path, command_id, params, initiator_view ):
        assert isinstance(initiator_view, View), repr(initiator_view)
        Request.__init__(self, iface, path, command_id, params)
        self.initiator_view_wr = weakref.ref(initiator_view)

    def process_response( self, server, response ):
        assert isinstance(response.result, tHandle), repr(response.result)
        handle = response.result
        handle = ProxyObjectMapper.map(handle, proxy_registry, server)
        redirect_handles = RedirectHandleCollector.collect(handle)
        if redirect_handles:
            self.run_resolve_redirect_request(handle, redirect_handles)
            return
        assert isinstance(handle, tViewHandle), repr(handle)
        self.open_handle(handle, server)

    def open_handle( self, handle, server ):
        view = self.initiator_view_wr()
        if not view:
            print 'Received response #%s for a missing (already destroyed) view, ignoring' % response.request_id
            return
        view.process_handle_open(handle, server)

    def run_resolve_redirect_request( self, handle, redirect_handles ):
        assert len(redirect_handles) == 1  # multiple redirects in one response is not supported (yet?)
        url = Url.from_data(iface_registry, redirect_handles[0].redirect_to)
        RedirectResolveRequest(url, orig_request=self, orig_handle=handle).execute()

    def redirect_resolved( self, handle, map_to_handle, server ):
        resolved_handle = RedirectHandleMapper.map(handle, [map_to_handle])
        self.open_handle(resolved_handle, server)


class GetRequestBase(Request):

    def __init__( self, url ):
        assert isinstance(url, Url), repr(url)
        command_id = 'get'
        Request.__init__(self, url.iface, url.path, command_id)
        self.endpoint = url.endpoint

    def execute( self ):
        server = Server.produce(self.endpoint)
        server.execute_request(self)

        
class RedirectResolveRequest(GetRequestBase):

    def __init__( self, url, orig_request, orig_handle ):
        assert isinstance(orig_request, OpenRequest), repr(orig_request)
        assert isinstance(orig_handle, tHandle), repr(orig_handle)
        GetRequestBase.__init__(self, url)
        self.orig_request = orig_request
        self.orig_handle = orig_handle

    def process_response( self, server, response ):
        handle = response.result
        assert isinstance(handle, tViewHandle), repr(handle)
        self.orig_request.redirect_resolved(self.orig_handle, handle, server)


# todo: must support redirects, same as OpenRequest - get request may be issued for redirecting or having nested redirect ref        
class GetRequest(GetRequestBase):

    def __init__( self, url, view ):
        assert isinstance(view, View), repr(view)
        GetRequestBase.__init__(self, url)
        self.initiator_view_wr = weakref.ref(view)
        
    def process_response( self, server, response ):
        handle = response.result
        assert isinstance(handle, tViewHandle), repr(handle)

        view = self.initiator_view_wr()
        if not view:
            print 'Received response #%s for a missing (already destroyed) view, ignoring' % response.request_id
            return
        view.process_handle_open(handle, server)


class ProxyObject(Object):

    @classmethod
    def produce_obj_by_objinfo( cls, objinfo, server=None ):
        assert isinstance(objinfo, tThisProxyObject), repr(objinfo)
        if isinstance(objinfo, tProxyObject):
            server = Server.produce(Endpoint.from_data(objinfo.endpoint))
        else:
            assert server is not None, repr(objinfo)  # we need endpoint somehow
        iface = iface_registry.resolve(objinfo.iface)
        facets = [iface_registry.resolve(facet) for facet in objinfo.facets]
        object = cls.produce_obj(server, objinfo.path, iface, facets)
        if isinstance(objinfo, tThisProxyObjectWithContents):  # is it a response?
            object.set_contents(objinfo.contents)
        return object

    # we avoid making proxy objects with same server+path
    @classmethod
    def produce_obj( cls, server, path, iface, facets ):
        object = proxy_registry.resolve(server, path)
        if object is not None:
            print '> proxy object is resolved from registry:', object
            return object
        object = cls(server, path, iface, facets)
        proxy_registry.register(server, path, object)
        print '< proxy object is registered in registry:', object
        return object

    def __init__( self, server, path, iface, facets=None ):
        assert is_list_inst(path, basestring), repr(path)
        assert isinstance(iface, Interface), repr(iface)
        assert facets is None or is_list_inst(facets, Interface), repr(facets)
        Object.__init__(self)
        self.server = server
        self.path = path
        self.iface = iface
        self.facets = facets or []
        self.cache = cache_repository
        cached_commands = self.cache.load_value(self._get_commands_cache_key(), self._get_commands_cache_type())
        self.commands = map(Command.from_data, cached_commands or [])

    def __repr__( self ):
        return 'ProxyObject(%s, %s, %s)' % (self.server.endpoint.public_key.get_short_id_hex(), self.iface.iface_id, '|'.join(self.path))

    def to_data( self ):
        return tProxyObject(
            self.get_objimpl_id(),
            self.iface.iface_id,
            [facet.iface_id for facet in self.facets],
            self.path,
            self.server.get_endpoint().to_data(),
            )

    def get_url( self ):
        return self.server.make_url(self.iface, self.path)

    def get_module_ids( self ):
        return self.iface.get_module_ids()

    @classmethod
    def get_objimpl_id( cls ):
        return 'object'

    def server_subscribe( self ):
        self.execute_request('subscribe')

    def set_contents( self, contents ):
        self.commands = map(Command.from_data, contents.commands)
        self.cache.store_value(self._get_commands_cache_key(), contents.commands, self._get_commands_cache_type())

    def get_title( self ):
        return '%s:%s' % (self.server.endpoint.public_key.get_short_id_hex(), '|'.join(self.path))

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
        return ClientNotification(self.iface, self.path, command_id, params=params)

    def prepare_request( self, command_id, initiator_view, *args, **kw ):
        params = self.iface.make_params(command_id, *args, **kw)
        if self.iface.is_open_command(command_id) and initiator_view:
            return OpenRequest(self.iface, self.path, command_id, params, initiator_view)
        else:
            return RequestForResult(self, command_id, params)

    def send_notification( self, command_id, *args, **kw ):
        request = self.prepare_notification(command_id, *args, **kw)
        self.server.send_notification(request)

    def execute_request( self, command_id, initiator_view=None, *args, **kw ):
        request = self.prepare_request(command_id, initiator_view, *args, **kw)
        self.server.execute_request(request)

    def process_response_result( self, command_id, result ):
        if command_id == 'subscribe':
            self.process_subscribe_response(result)

    def process_subscribe_response( self, result ):
        self.set_contents(result)
        self._notify_object_changed()

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)

    def _get_commands_cache_key( self ):
        return self.make_cache_key('commands')

    def make_cache_key( self, name ):
        return ['object', self.server.get_id().encode('hex')] + self.path + [name]

    def _get_commands_cache_type( self ):
        return TList(tCommand)

    def __del__( self ):
        print '~ProxyObject', self, self.path


proxy_class_registry.register(ProxyObject)
