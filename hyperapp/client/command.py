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

    @classmethod
    def from_data( cls, rec ):
        return cls(rec.id, rec.text, rec.desc, rec.shortcut)

    def __init__( self, text, desc, shortcut=None, enabled=True ):
        assert isinstance(text, str), repr(text)
        assert isinstance(desc, str), repr(desc)
        assert (shortcut is None
                or isinstance(shortcut, str)
                or is_list_inst(shortcut, str)), repr(shortcut)
        assert isinstance(enabled, bool), repr(enabled)
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.enabled = enabled

    def is_enabled( self ):
        return self.enabled

    def set_enabled( self, enabled ):
        if enabled == self.enabled: return
        self.enabled = enabled
        view = self._view_wr()
        if view:
            view.view_changed()

    def enable( self ):
        self.set_enabled(True)

    def disable( self ):
        self.set_enabled(False)

    def clone_without_shortcuts( self, shortcut_set ):
        new_shortcuts = set(self.get_shortcut_list()) - shortcut_set
        return self.clone(shortcut=list(new_shortcuts))

    @abc.abstractmethod
    def get_inst( self ):
        pass

    @abc.abstractmethod
    def clone( self, shortcut=None ):
        pass
    
    # returns basestring list
    def get_shortcut_list( self ):
        if isinstance(self.shortcut, str):
            return [self.shortcut]
        else:
            return self.shortcut or []

    ## def to_data( self ):
    ##     return tCommand(self.id, self.text, self.desc, self.shortcut)

    def make_action( self, widget ):
        log.debug('Command.make_action: %r, %r', self, self.run)
        action = make_async_action(widget, self.text, self.shortcut, self.run)
        action.setEnabled(self.enabled)
        return action

    @asyncio.coroutine
    @abc.abstractmethod
    def run( self, *args, **kw ):
        pass


class ViewCommand(Command):

    @classmethod
    def from_command( cls, cmd, view ):
        return cls(cmd.text, cmd.desc, cmd.shortcut, cmd.enabled, cmd, weakref.ref(view))

    def __init__( self, text, desc, shortcut, enabled, base_cmd, view_wr ):
        Command.__init__(self, text, desc, shortcut, enabled)
        self._base_cmd = base_cmd
        self._view_wr = view_wr  # weak ref to class instance

    def get_inst( self ):
        return self._view_wr()

    def clone( self, shortcut=None ):
        if shortcut is None:
            shortcut = self.shortcut
        return ViewCommand(self.text, self.desc, shortcut, self.enabled, self._base_cmd, self._view_wr)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        view = self._view_wr()
        print('ViewCommand.run', self, view)
        if not view: return
        handle = yield from self._base_cmd.run(*args, **kw)
        print(' ->', handle)
        assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            view.open(handle)


class WindowCommand(Command):

    @classmethod
    def from_command( cls, cmd, window ):
        return cls(cmd.text, cmd.desc, cmd.shortcut, cmd.enabled, cmd, weakref.ref(window))

    def __init__( self, text, desc, shortcut, enabled, base_cmd, window_wr ):
        Command.__init__(self, text, desc, shortcut, enabled)
        self._base_cmd = base_cmd
        self._window_wr = window_wr  # weak ref to class instance

    def get_inst( self ):
        return self._window_wr()

    def clone( self, shortcut=None ):
        if shortcut is None:
            shortcut = self.shortcut
        return WindowCommand(self.text, self.desc, shortcut, self.enabled, self._base_cmd, self._window_wr)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        window = self._window_wr()
        print('WindowCommand.run', self, window)
        if not window: return
        handle = yield from self._base_cmd.run(*args, **kw)
        print(' ->', handle)
        assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            window.get_current_view().open(handle)


class BoundCommand(Command):

    def __init__( self, text, desc, shortcut, enabled, class_method, inst_wr, args=None ):
        Command.__init__(self, text, desc, shortcut, enabled)
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance
        self._args = args or ()

    def get_inst( self ):
        return self._inst_wr()

    def clone( self, shortcut=None, args=None ):
        if shortcut is None:
            shortcut = self.shortcut
        if args is None:
            args = self._args
        else:
            args = self._args + args
        return BoundCommand(self.text, self.desc, shortcut, self.enabled, self._class_method, self._inst_wr, args)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        inst = self._inst_wr()
        print('BoundCommand.run', self, inst, self._args)
        if not inst: return  # inst is deleteddeleted
        if asyncio.iscoroutinefunction(self._class_method):
            return (yield from self._class_method(ins, *(self._args + args), **kw))
        else:
            return self._class_method(inst, *(self._args + args), **kw)


class UnboundCommand(object):

    def __init__( self, text, desc, shortcut, enabled, class_method ):
        assert isinstance(text, str), repr(text)
        assert isinstance(desc, str), repr(desc)
        assert (shortcut is None
                or isinstance(shortcut, str)
                or is_list_inst(shortcut, str)), repr(shortcut)
        assert isinstance(enabled, bool), repr(enabled)
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.enabled = enabled
        self._class_method = class_method

    def bind( self, inst ):
        return BoundCommand(self.text, self.desc, self.shortcut, self.enabled, self._class_method, weakref.ref(inst))


# decorator for view methods
class command(object):

    def __init__( self, text, desc, shortcut=None, enabled=True ):
        assert isinstance(text, str), repr(text)
        assert isinstance(desc, str), repr(desc)
        assert (shortcut is None
                or isinstance(shortcut, str)
                or is_list_inst(shortcut, str)), repr(shortcut)
        assert isinstance(enabled, bool), repr(enabled)
        self.text = text
        self.desc = desc
        self.shortcut = shortcut  # basestring for single shortcut, basestring list for multiple
        self.enabled = enabled

    def __call__( self, class_method ):
        return UnboundCommand(self.text, self.desc, self.shortcut, self.enabled, class_method)


class Commandable(object):

    def __init__( self ):
        self._commands = []  # BoundCommand list
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, UnboundCommand): continue
            bound_cmd = attr.bind(self)
            setattr(self, name, bound_cmd)  # set_enabled must change command for this view, not for all of them
            self._commands.append(bound_cmd)

    def get_commands( self ):
        return self._commands
