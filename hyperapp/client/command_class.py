import logging
import asyncio
import weakref
import abc
from ..common.htypes import tResourceId

log = logging.getLogger(__name__)


# returned from Object.get_commands
class Command(object, metaclass=abc.ABCMeta):

    def __init__( self, id, kind, resource_id, is_default_command=False, enabled=True ):
        assert isinstance(id, str), repr(id)
        assert isinstance(kind, str), repr(kind)
        assert isinstance(resource_id, tResourceId), repr(resource_id)
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

    def __init__( self, id, kind, resource_id, is_default_command, enabled, class_method ):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(resource_id, tResourceId), repr(resource_id)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self._resource_id = resource_id
        self.is_default_command = is_default_command
        self.enabled = enabled
        self._class_method = class_method

    def bind( self, inst, kind ):
        if self.kind is not None:
            kind = self.kind
        return BoundCommand(self.id, kind, self._resource_id, self.is_default_command, self.enabled, self._class_method, weakref.ref(inst))


class Commander(object):

    def __init__( self, commands_kind ):
        if hasattr(self, '_commands'):  # multiple inheritance hack
            return  # do not populate _commands twice
        self._commands_kind = commands_kind
        self._commands = []  # BoundCommand list
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, UnboundCommand): continue
            bound_cmd = attr.bind(self, commands_kind)
            setattr(self, name, bound_cmd)  # set_enabled must change command for this view, not for all of them
            self._commands.append(bound_cmd)

    def get_command( self, command_id ):
        for command in self._commands:
            assert isinstance(command, BoundCommand), repr(command)
            if command.id == command_id:
                return command
        return None

    def get_commands( self, kinds=None ):
        if kinds is None:
            kinds = set([self._commands_kind])
        return [cmd for cmd in self._commands if cmd.kind in kinds]
