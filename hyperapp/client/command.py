import logging
import asyncio
import weakref
import abc
from ..common.util import is_list_inst
from ..common.htypes import tCommand
from .util import make_async_action

log = logging.getLogger(__name__)


class CommandBase(object):

    def __init__( self, text, desc, shortcut ):
        assert isinstance(text, str), repr(text)
        assert isinstance(desc, str), repr(desc)
        assert (shortcut is None
                or isinstance(shortcut, str)
                or is_list_inst(shortcut, str)), repr(shortcut)
        self.text = text
        self.desc = desc
        self.shortcut = shortcut  # basestring for single shortcut, basestring list for multiple


# returned from Object.get_commands
class Command(CommandBase):

    @classmethod
    def from_data( cls, rec ):
        return cls(rec.id, rec.text, rec.desc, rec.shortcut)

    def __init__( self, id, text, desc, shortcut=None ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def to_data( self ):
        return tCommand(self.id, self.text, self.desc, self.shortcut)

    def as_object_command( self, view ):
        return ObjectCommand(view, self.id, self.text, self.desc, self.shortcut)


class RunnableCommand(Command, metaclass=abc.ABCMeta):

    def make_action( self, widget ):
        log.debug('RunnableCommand.make_action: %r %r, %r', self.id, self, self.run)
        return make_async_action(widget, self.text, self.shortcut, self.run)

    @asyncio.coroutine
    @abc.abstractmethod
    def run( self ):
        pass


# returned from View.get_object_commands
class ObjectCommand(RunnableCommand):

    def __init__( self, view, id, text, desc, shortcut=None ):
        RunnableCommand.__init__(self, id, text, desc, shortcut)
        self.view_wr = weakref.ref(view)  # View or Module

    @asyncio.coroutine
    def run( self ):
        view = self.view_wr()
        if not view: return
        yield from view.run_object_command(self.id)


# stored in Element.commands            
class ElementCommand(Command):

    def make_action( self, widget, view, element_key ):
        return make_async_action(widget, self.text, self.shortcut, self.run, weakref.ref(view), element_key)

    @asyncio.coroutine
    def run( self, view_wr, element_key ):
        view = view_wr()
        if view:
            yield from view.run_object_element_command(self.id, element_key)
