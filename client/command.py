import weakref
from util import is_list_inst, make_action
import view_registry


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

    def run_with_weaks( self, view_wref, obj_wref, element_key ):
        return self.run(view_wref(), obj_wref(), element_key)

    def run( self, view, obj, element_key ):
        print 'ElementCommand.run', self.id, obj, view, element_key
        handle = obj.run_element_command(self.id, element_key)
        if handle:
            view.open(handle)

    def make_action( self, widget, view, obj, element_key ):
        return self._make_action(widget, weakref.ref(view), weakref.ref(obj), element_key)


class ModuleCommand(Command):

    def __init__( self, id, text, desc, shortcut, module_name ):
        Command.__init__(self, id, text, desc, shortcut)
        self.module_name = module_name

    @classmethod
    def from_json( cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'], data['module_name'])

    def run_with_weaks( self, window_wref, app ):
        return self.run(window_wref(), app)

    def run( self, window, app ):
        print 'ModuleCommand.run', self.id, self.module_name, window, app
        request = dict(
            method='run_command',
            path=dict(module=self.module_name),
            command_id=self.id)
        handle = app.server.request_an_object(request)
        if handle:
            window.current_view().open(handle)

    def make_action( self, widget, window, app ):
        return self._make_action(widget, weakref.ref(window), app)
