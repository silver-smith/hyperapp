import weakref
from .util import make_action


class CommandBase(object):

    def __init__( self, text, desc, shortcut ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut


class Command(CommandBase):

    @classmethod
    def decode( cls, rec ):
        return cls(rec.id, rec.text, rec.desc, rec.shortcut)

    def __init__( self, id, text, desc, shortcut=None ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def as_object_command( self, view ):
        return ObjectCommand(view, self.id, self.text, self.desc, self.shortcut)


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


class ElementCommand(Command):

    def make_action( self, widget, view, element_key ):
        return make_action(widget, self.text, self.shortcut, self.run, weakref.ref(view), element_key)

    def run( self, view_wr, element_key ):
        view = view_wr()
        if view:
            view.run_object_element_command(self.id, element_key)
