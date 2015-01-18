from util import make_action
import view_registry


class Command(object):

    def __init__( self, id, text, desc, shortcut ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    @classmethod
    def from_json( cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'])

    def _make_action( self, widget, *args ):
        return make_action(widget, self.text, self.shortcut, self.run, *args)


class ObjectCommand(Command):

    def run( self, view, obj ):
        print 'ObjectCommand.run', self.id, obj, view
        handle = obj.run_command(self.id)
        if handle:
            view.open(handle)

    def make_action( self, widget, view, obj ):
        return self._make_action(widget, view, obj)


class ElementCommand(Command):

    def run( self, view, obj, element_key ):
        print 'ElementCommand.run', self.id, obj, view, element_key
        request = dict(
            method='run_element_command',
            path=obj.path,
            command_id=self.id,
            element_key=element_key,
            )
        handle = obj.server.get_view(request)
        if handle:
            view.open(handle)

    def make_action( self, widget, view, obj, element_key ):
        return self._make_action(widget, view, obj, element_key)


class ModuleCommand(Command):

    def __init__( self, id, text, desc, shortcut, module_name ):
        Command.__init__(self, id, text, desc, shortcut)
        self.module_name = module_name

    @classmethod
    def from_json( cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'], data['module_name'])

    def run( self, window, app ):
        print 'ModuleCommand.run', self.id, self.module_name, window, app
        request = dict(
            method='run_module_command',
            module_name=self.module_name,
            command_id=self.id)
        handle = app.server.get_view(request)
        if handle:
            window.current_view().open(handle)

    def make_action( self, widget, window, app ):
        return self._make_action(widget, window, app)
