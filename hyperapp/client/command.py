import weakref
from ..common.htypes import tCommand
from .util import make_action


class CommandBase(object):

    def __init__( self, text, desc, shortcut ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut


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
        return tCommand.instantiate(self.id, self.text, self.desc, self.shortcut)

    def as_object_command( self, view ):
        return ObjectCommand(view, self.id, self.text, self.desc, self.shortcut)


# returned from View.get_object_commands
class ObjectCommand(Command):

    def __init__( self, view, id, text, desc, shortcut=None ):
        Command.__init__(self, id, text, desc, shortcut)
        self.view_wr = weakref.ref(view)

    def make_action( self, widget ):
        return make_action(widget, self.text, self.shortcut, self.run, self.view_wr)

    def run( self, view_wr ):
        view = view_wr()
        if view:
            view.run_object_command(self.id)


# stored in Element.commands            
class ElementCommand(Command):

    def make_action( self, widget, view, element_key ):
        return make_action(widget, self.text, self.shortcut, self.run, weakref.ref(view), element_key)

    def run( self, view_wr, element_key ):
        view = view_wr()
        if view:
            view.run_object_element_command(self.id, element_key)
