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
        request = dict(
            method='run_dir_command',
            path=obj.path,
            command_id=self.id,
            )
        new_obj = obj.server.get_object(request)
        if new_obj:
            self.open_obj(view, new_obj)

    def make_action( self, widget, view, obj ):
        return make_action(widget, self.text, self.shortcut, self.run, view, obj)


class ElementCommand(Command):

    def run( self, view, obj, element_key ):
        print 'list_obj.Command.run_element_command', obj, view
        request = dict(
            method='run_element_command',
            path=obj.path,
            command_id=self.id,
            element_key=element_key,
            )
        new_obj = obj.server.get_object(request)
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
            module_name=self.module_name,
            command_id=self.id)
        response = app.server.execute_request(request)
        obj = app.server.get_object(request)
        if obj:
            self.open_obj(window, obj)

    def make_action( self, widget, window, app ):
        return make_action(widget, self.text, self.shortcut, self.run, window, app)
