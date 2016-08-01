import logging
import asyncio
import weakref
import abc
from ..common.util import is_list_inst
from ..common.htypes import tCommand, tHandle
from .util import make_async_action

log = logging.getLogger(__name__)


# returned from Object.get_commands
class Command(object, metaclass=abc.ABCMeta):

    def __init__( self, id, kind, resource_id, is_default_command=False, enabled=True ):
        assert isinstance(id, str), repr(id)
        assert isinstance(kind, str), repr(kind)
        assert isinstance(resource_id, str), repr(resource_id)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self.resource_id = resource_id
        self.is_default_command = is_default_command
        self.enabled = enabled

    def __repr__( self ):
        return '%s(%r)' % (self.__class__.__name__, self.id)

    def is_enabled( self ):
        return self.enabled

    def set_enabled( self, enabled ):
        if enabled == self.enabled: return
        self.enabled = enabled
        view = self.get_view()
        if view:
            view.view_changed()

    def enable( self ):
        self.set_enabled(True)

    def disable( self ):
        self.set_enabled(False)

    @abc.abstractmethod
    def get_view( self ):
        pass

    @abc.abstractmethod
    def clone( self ):
        pass
    
    @asyncio.coroutine
    @abc.abstractmethod
    def run( self, *args, **kw ):
        pass


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
        handle = yield from self._base_cmd.run(*args, **kw)
        assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
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
        handle = yield from self._base_cmd.run(*args, **kw)
        assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            window.get_current_view().open(handle)


class BoundCommand(Command):

    def __init__( self, id, kind, resource_id, is_default_command, enabled, class_method, inst_wr, args=None ):
        Command.__init__(self, id, kind, resource_id, is_default_command, enabled)
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance
        self._args = args or ()

    def __repr__( self ):
        return 'BoundCommand(%r/%r -> %r, args=%r)' % (self.id, self.kind, self._inst_wr, self._args)

    def get_view( self ):
        return self._inst_wr()

    def clone( self, args=None ):
        if args is None:
            args = self._args
        else:
            args = self._args + args
        return BoundCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._class_method, self._inst_wr, args)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        inst = self._inst_wr()
        if not inst: return  # inst is deleteddeleted
        log.debug('BoundCommand.run: %s, %r/%r, %r, (%s/%s, %s)', self, self.id, self.kind, inst, self._args, args, kw)
        if asyncio.iscoroutinefunction(self._class_method):
            return (yield from self._class_method(inst, *(self._args + args), **kw))
        else:
            return self._class_method(inst, *(self._args + args), **kw)


class UnboundCommand(object):

    def __init__( self, id, kind, module_name, is_default_command, enabled, class_method ):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(module_name, str), repr(module_name)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self._module_name = module_name
        self.is_default_command = is_default_command
        self.enabled = enabled
        self._class_method = class_method

    def bind( self, inst, kind ):
        if self.kind is not None:
            kind = self.kind
        return BoundCommand(self.id, kind, self._module_name, self.is_default_command, self.enabled, self._class_method, weakref.ref(inst))


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
        ## print('### command module:', module_name)
        return UnboundCommand(self.id, self.kind, module_name, self.is_default_command, self.enabled, class_method)


class Commander(object):

    def __init__( self, commands_kind ):
        if hasattr(self, '_commands'):  # multiple inheritance hack
            return  # do not populate _commands twice
        self._commands = []  # BoundCommand list
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, UnboundCommand): continue
            bound_cmd = attr.bind(self, commands_kind)
            setattr(self, name, bound_cmd)  # set_enabled must change command for this view, not for all of them
            if bound_cmd.kind == commands_kind:
                self._commands.append(bound_cmd)

    def get_command( self, command_id ):
        for command in self.get_commands():
            if command.id == command_id:
                return command
        return None

    def get_commands( self ):
        return self._commands
