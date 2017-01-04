import logging
import asyncio
import weakref
from ..common.htypes import Field, TRecord
from .command_class import Command, UnboundCommand
from .module import Module

log = logging.getLogger(__name__)


class ViewCommand(Command):

    @classmethod
    def from_command( cls, cmd, view ):
        return cls(cmd.id, cmd.kind, cmd.resource_id, cmd.is_default_command, cmd.enabled, cmd, weakref.ref(view))

    def __init__( self, id, kind, resource_id, is_default_command, enabled, base_cmd, view_wr ):
        Command.__init__(self, id, kind, resource_id, is_default_command, enabled)
        self._base_cmd = base_cmd
        self._view_wr = view_wr  # weak ref to class instance

    def __repr__( self ):
        return 'ViewCommand(%r -> %r)' % (self.id, self._view_wr)

    def get_view( self ):
        return self._view_wr()

    def clone( self ):
        return ViewCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._base_cmd, self._window_wr)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        view = self._view_wr()
        if not view: return
        log.debug('ViewCommand.run: %r/%r, %r, (%s, %s)', self.id, self.kind, self._base_cmd, args, kw)
        handle = (yield from self._base_cmd.run(*args, **kw)).handle
        ## assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            view.open(handle)


class WindowCommand(Command):

    @classmethod
    def from_command( cls, cmd, window ):
        return cls(cmd.id, cmd.kind, cmd.resource_id, cmd.is_default_command, cmd.enabled, cmd, weakref.ref(window))

    def __init__( self, id, kind, resource_id, is_default_command, enabled, base_cmd, window_wr ):
        Command.__init__(self, id, kind, resource_id, is_default_command, enabled)
        self._base_cmd = base_cmd
        self._window_wr = window_wr  # weak ref to class instance

    def __repr__( self ):
        return 'WindowCommand(%r -> %r)' % (self.id, self._base_cmd)

    def get_view( self ):
        return self._window_wr()

    def clone( self ):
        return WindowCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._base_cmd, self._window_wr)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        window = self._window_wr()
        if not window: return
        log.debug('WindowCommand.run: %r/%r, %r, (%s, %s)', self.id, self.kind, self._base_cmd, args, kw)
        handle = (yield from self._base_cmd.run(*args, **kw)).handle
        ## assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            window.get_current_view().open(handle)


# decorator for view methods
class command(object):

    def __init__( self, id, kind=None, enabled=True, is_default_command=False ):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self.is_default_command = is_default_command
        self.enabled = enabled

    def __call__( self, class_method ):
        module_name = class_method.__module__.split('.')[-1]
        resource_id = ['client_module', module_name]
        ## print('### command module:', module_name)
        return UnboundCommand(self.id, self.kind, resource_id,
                              self.is_default_command, self.enabled, self.wrap_method(class_method))

    def wrap_method( self, method ):
        return method


# commands returning handle to open
class open_command(command):

    def wrap_method( self, method ):
        def fn(*args, **kw):
            handle = method(*args, **kw)
            return this_module.open_command_result(handle)
        return fn


class ThisModule(Module):

    def __init__( self, services ):
        Module.__init__(self, services)
        self.open_command_result = TRecord([Field('handle', services.core_types.handle)])
