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

    def open_obj( self, view, obj ):
        handle_ctr = view_registry.resolve_view('list')  # hardcoded for now
        view.open(handle_ctr(obj))


class DirCommand(Command):

    def run( self, view, obj ):
        print 'list_obj.Command.run_dir_command', obj, view
        new_obj = obj.run_dir_command(self.id)
        if new_obj:
            self.open_obj(view, new_obj)

    def make_action( self, widget, view, obj ):
        return make_action(widget, self.text, self.shortcut, self.run, view, obj)


class ElementCommand(Command):

    def run( self, view, obj, element_key ):
        print 'list_obj.Command.run_element_command', obj, view
        new_obj = obj.run_element_command(self.id, element_key)
        if new_obj:
            self.open_obj(view, new_obj)

    def make_action( self, widget, view, obj, element_key ):
        return make_action(widget, self.text, self.shortcut, self.run, view, obj, element_key)


class ModuleCommand(Command):

    def __init__( self, id, text, desc, shortcut, module_name ):
        Command.__init__(self, id, text, desc, shortcut)
        self.module_name = module_name

    @classmethod
    def from_json( cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'], data['module_name'])

    def run( self, window, app ):
        request = dict(
            method='run_module_command',
            command_id=self.id)
        response = app.connection.execute_request(request)
        # todo

    def make_action( self, widget, window, app ):
        return make_action(widget, self.text, self.shortcut, self.run, window, app)
