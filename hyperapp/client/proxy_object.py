import logging
import asyncio
import uuid
import weakref
import codecs
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    IfaceCommand,
    Interface,
    TList,
    Field,
    tString,
    TOptional,
    TRecord,
    tCommand,
    tPath,
    )
from ..common.identity import PublicKey
from ..common.url import Url
from .object import Object
from .command import Command
from .request import ClientNotification, Request
from .server import Server
from .view import View

log = logging.getLogger(__name__)


def register_object_implementations( registry, services ):
    ProxyObject.register(registry, services)


@asyncio.coroutine
def execute_get_request( request_types, remoting, url ):
    assert isinstance(url, Url), repr(url)
    server = Server.from_public_key(remoting, url.public_key)
    request_id = str(uuid.uuid4())
    command_id = 'get'
    params = url.iface.make_params(command_id)
    request = Request(request_types, url.iface, url.path, command_id, request_id, params)
    response = yield from server.execute_request(request)
    return response.result


class RemoteCommand(Command):

    def __init__( self, id, kind, module_name, is_default_command, enabled, object_wr, args=None ):
        assert isinstance(object_wr(), ProxyObject), repr(object_wr)
        Command.__init__(self, id, kind, module_name, is_default_command, enabled)
        self._object_wr = object_wr
        self._args = args or ()

    def __repr__( self ):
        return 'RemoteCommand(%r)' % self.id

    def to_data( self ):
        return tCommand(self.id, self.kind, self.resource_id)

    def get_view( self ):
        return None

    def clone( self, args=None ):
        args = self._args + (args or ())
        return RemoteCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._object_wr, args)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        object = self._object_wr()
        if not object: return
        return (yield from object.run_remote_command(self.id, *(self._args + args), **kw))


class ProxyObject(Object):

    objimpl_id = 'proxy'

    @classmethod
    def register( cls, registry, services ):
        registry.register(cls.objimpl_id, cls.from_state, services.request_types, services.core_types,
                          services.iface_registry, services.remoting, services.proxy_registry, services.cache_repository)

    @classmethod
    def from_state( cls, state, request_types, core_types, iface_registry, remoting, proxy_registry, cache_repository ):
        assert isinstance(state, core_types.proxy_object), repr(state)
        server_public_key = PublicKey.from_der(state.public_key_der)
        server = Server.from_public_key(remoting, server_public_key)
        iface = iface_registry.resolve(state.iface)
        facets = [iface_registry.resolve(facet) for facet in state.facets]
        object = cls.produce_obj(request_types, core_types, iface_registry, proxy_registry, cache_repository, server, state.path, iface, facets)
        if isinstance(state, core_types.proxy_object_with_contents):  # is it a response?
            object.set_contents(state.contents)
        return object

    # we avoid making proxy objects with same server+path
    @classmethod
    def produce_obj( cls, request_types, core_types, iface_registry, proxy_registry, cache_repository, server, path, iface, facets ):
        object = proxy_registry.resolve(server, path)
        if object is not None:
            log.info('> proxy object is resolved from registry: %r', object)
            return object
        object = cls(request_types, core_types, iface_registry, cache_repository, server, path, iface, facets)
        proxy_registry.register(server, path, object)
        log.info('< proxy object is registered in registry: %r', object)
        return object

    def __init__( self, request_types, core_types, iface_registry, cache_repository, server, path, iface, facets=None ):
        assert is_list_inst(path, str), repr(path)
        assert isinstance(iface, Interface), repr(iface)
        assert facets is None or is_list_inst(facets, Interface), repr(facets)
        Object.__init__(self)
        self._request_types = request_types
        self._core_types = core_types
        self.iface_registry = iface_registry
        self.server = server
        self.path = path
        self.iface = iface
        self.facets = facets or []
        self.cache_repository = cache_repository
        cached_commands = self.cache_repository.load_value(self._get_commands_cache_key(), self._get_commands_cache_type())
        self._remote_commands = [self._remote_command_from_iface_command(cmd) for cmd in self.iface.get_commands()
                                 if self._is_plain_open_handle_request(cmd)]

    def __repr__( self ):
        return 'ProxyObject(%s, %s, %s)' % (self.server.public_key.get_short_id_hex(), self.iface.iface_id, '|'.join(self.path))

    def get_state( self ):
        return self._core_types.proxy_object(
            objimpl_id=self.objimpl_id,
            public_key_der=self.server.public_key.to_der(),
            iface=self.iface.iface_id,
            facets=[facet.iface_id for facet in self.facets],
            path=self.path,
            )

    def get_url( self ):
        return self.server.make_url(self.iface, self.path)

    def get_facets( self ):
        return self.facets

    @asyncio.coroutine
    def server_subscribe( self ):
        result = yield from self.execute_request('subscribe')
        self.set_contents(result)
        self._notify_object_changed()

    def set_contents( self, contents ):
        #self._remote_commands = list(map(self._command_from_data, contents.commands))
        self.cache_repository.store_value(self._get_commands_cache_key(), contents.commands, self._get_commands_cache_type())

    def get_title( self ):
        return '%s:%s' % (self.server.public_key.get_short_id_hex(), '|'.join(self.path))

    def get_commands( self ):
        return Object.get_commands(self) + self._remote_commands

    @asyncio.coroutine
    def run_remote_command( self, command_id, *args, **kw ):
        log.debug('running remote command %r (*%s, **%s)', command_id, args, kw)
        return (yield from self.execute_request(command_id, *args, **kw))

    def observers_gone( self ):
        log.info('-- observers_gone: %r', self)
        asyncio.async(self.send_notification('unsubscribe'))

    # prepare request which does not require/expect response
    def prepare_notification( self, command_id, *args, **kw ):
        params = self.iface.make_params(command_id, *args, **kw)
        return ClientNotification(self._request_types, self.iface, self.path, command_id, params=params)

    def prepare_request( self, command_id, *args, **kw ):
        request_id = str(uuid.uuid4())
        params = self.iface.make_params(command_id, *args, **kw)
        return Request(self._request_types, self.iface, self.path, command_id, request_id, params)

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

    def _command_from_data( self, rec ):
        return RemoteCommand(rec.command_id, rec.kind, rec.resource_id,
                             is_default_command=rec.is_default_command, enabled=True, object_wr=weakref.ref(self))

    def _is_plain_open_handle_request( self, cmd ):
        t_open_result = TRecord([
            Field('handle', TOptional(self._core_types.handle)),
            ])
        return (cmd.request_type == IfaceCommand.rt_request
                and cmd.get_params_type(self.iface).get_fields() == []
                and cmd.get_result_type(self.iface) == t_open_result)

    def _remote_command_from_iface_command( self, cmd ):
        kind = 'object'
        resource_id = ['interface', self.iface.iface_id, cmd.command_id]
        return RemoteCommand(cmd.command_id, kind, resource_id,
                             is_default_command=False, enabled=True, object_wr=weakref.ref(self))

    def _get_commands_cache_key( self ):
        return self.make_cache_key('commands')

    def make_cache_key( self, name ):
        return [self.objimpl_id, self.server.public_key.get_id_hex()] + self.path + [name]

    def _get_commands_cache_type( self ):
        return TList(tCommand)

    def __del__( self ):
        log.info('~ProxyObject %r path=%r', self, self.path)
