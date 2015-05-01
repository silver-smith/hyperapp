import weakref
from util import is_list_inst, make_action


class Command(object):

    def __init__( self, id, text, desc, shortcut ):
        assert shortcut is None or isinstance(shortcut, basestring) or is_list_inst(shortcut, basestring), repr(shortcut)
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut  # basestring for single shortcut, basestring list for multiple

    @classmethod
    def from_json( cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'])

    def _make_action( self, widget, *args ):
        return make_action(widget, self.text, self.shortcut, self.run_with_weaks, *args)


class ObjectCommand(Command):

    def run_with_weaks( self, view_wref ):
        return self.run(view_wref())

    def run( self, view ):
        print 'ObjectCommand.run', self.id, view
        view.run_object_command(self.id)

    def make_action( self, widget, view ):
        return self._make_action(widget, weakref.ref(view))


class ElementCommand(Command):

    def run_with_weaks( self, view_wref, element_key ):
        return self.run(view_wref(), element_key)

    def run( self, view, element_key ):
        print 'ElementCommand.run', self.id, view, element_key
        view.run_object_element_command(self.id, element_key)

    def make_action( self, widget, view, element_key ):
        return self._make_action(widget, weakref.ref(view), element_key)
