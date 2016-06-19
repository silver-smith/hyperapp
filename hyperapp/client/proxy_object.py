import logging
import asyncio
import uuid
import weakref
import codecs
from ..common.util import is_list_inst
from ..common.htypes import (
    Interface,
    TList,
    Field,
    tString,
    TRecord,
    tCommand,
    tObject,
    tProxyObject,
    tProxyObjectWithContents,
    tHandle,
    tViewHandle,
    tPath,
    tEndpoint,
    resolve_iface,
    iface_registry,
    )
from ..common.identity import PublicKey
from ..common.endpoint import Endpoint, Url
from .object import Object
from .command import Command
from .objimpl_registry import objimpl_registry
from .proxy_registry import proxy_registry
from .request import ClientNotification, Request
from .server import Server
from .cache_repository import cache_repository
from .view import View

log = logging.getLogger(__name__)


@asyncio.coroutine
def execute_get_request( url ):
    assert isinstance(url, Url), repr(url)
    server = Server.from_endpoint(url.endpoint)
    request_id = str(uuid.uuid4())
    command_id = 'get'
    params = url.iface.make_params(command_id)
    request = Request(url.iface, url.path, command_id, request_id, params)
    response = yield from server.execute_request(request)
    return response.result


class ProxyObject(Object):

    @classmethod
    def from_state( cls, state ):
        assert isinstance(state, tProxyObject), repr(state)
        server_public_key = PublicKey.from_der(state.public_key_der)
        server = Server.from_public_key(server_public_key)
        iface = iface_registry.resolve(state.iface)
        facets = [iface_registry.resolve(facet) for facet in state.facets]
        object = cls.produce_obj(server, state.path, iface, facets)
        if isinstance(state, tProxyObjectWithContents):  # is it a response?
            object.set_contents(state.contents)
        return object

    # we avoid making proxy objects with same server+path
    @classmethod
    def produce_obj( cls, server, path, iface, facets ):
        object = proxy_registry.resolve(server, path)
        if object is not None:
            log.info('> proxy object is resolved from registry: %r', object)
            return object
        object = cls(server, path, iface, facets)
        proxy_registry.register(server, path, object)
        log.info('< proxy object is registered in registry: %r', object)
        return object

    def __init__( self, server, path, iface, facets=None ):
        assert is_list_inst(path, str), repr(path)
        assert isinstance(iface, Interface), repr(iface)
        assert facets is None or is_list_inst(facets, Interface), repr(facets)
        Object.__init__(self)
        self.server = server
        self.path = path
        self.iface = iface
        self.facets = facets or []
        self.cache = cache_repository
        cached_commands = self.cache.load_value(self._get_commands_cache_key(), self._get_commands_cache_type())
        self.commands = list(map(Command.from_data, cached_commands or []))

    def __repr__( self ):
        return 'ProxyObject(%s, %s, %s)' % (self.server.public_key.get_short_id_hex(), self.iface.iface_id, '|'.join(self.path))

    def get_state( self ):
        return tProxyObject(
            objimpl_id=self.get_objimpl_id(),
            public_key_der=self.server.public_key.to_der(),
            iface=self.iface.iface_id,
            facets=[facet.iface_id for facet in self.facets],
            path=self.path,
            )

    def get_url( self ):
        return self.server.make_url(self.iface, self.path)

    def get_facets( self ):
        return self.facets

    def get_module_ids( self ):
        return self.iface.get_module_ids()

    @classmethod
    def get_objimpl_id( cls ):
        return 'object'

    @asyncio.coroutine
    def server_subscribe( self ):
        result = yield from self.execute_request('subscribe')
        self.set_contents(result)
        self._notify_object_changed()

    def set_contents( self, contents ):
        self.commands = list(map(Command.from_data, contents.commands))
        self.cache.store_value(self._get_commands_cache_key(), contents.commands, self._get_commands_cache_type())

    def get_title( self ):
        return '%s:%s' % (self.server.public_key.get_short_id_hex(), '|'.join(self.path))

    def get_commands( self ):
        return self.commands

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        return (yield from self.execute_request(command_id, **kw))

    def observers_gone( self ):
        log.info('-- observers_gone: %r', self)
        asyncio.async(self.send_notification('unsubscribe'))

    # prepare request which does not require/expect response
    def prepare_notification( self, command_id, *args, **kw ):
        params = self.iface.make_params(command_id, *args, **kw)
        return ClientNotification(self.iface, self.path, command_id, params=params)

    def prepare_request( self, command_id, *args, **kw ):
        request_id = str(uuid.uuid4())
        params = self.iface.make_params(command_id, *args, **kw)
        return Request(self.iface, self.path, command_id, request_id, params)

    @asyncio.coroutine
    def send_notification( self, command_id, *args, **kw ):
        notification = self.prepare_notification(command_id, *args, **kw)
        yield from self.server.send_notification(notification)

    @asyncio.coroutine
    def execute_request( self, command_id, *args, **kw ):
        request = self.prepare_request(command_id, *args, **kw)
        response = yield from self.server.execute_request(request)
        return response.result

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)

    def _get_commands_cache_key( self ):
        return self.make_cache_key('commands')

    def make_cache_key( self, name ):
        return ['object', self.server.public_key.get_id_hex()] + self.path + [name]

    def _get_commands_cache_type( self ):
        return TList(tCommand)

    def __del__( self ):
        log.info('~ProxyObject %r path=%r', self, self.path)


objimpl_registry.register(ProxyObject.get_objimpl_id(), ProxyObject.from_state)
