import weakref
from .command import RunnableCommand


class ModuleCommand(RunnableCommand):

    @classmethod
    def from_command( cls, cmd, module, view, object ):
        return cls(cmd.id, cmd.text, cmd.desc, cmd.shortcut, module, view, object)

    def __init__( self, id, text, desc, shortcut, module, view, object ):
        RunnableCommand.__init__(self, id, text, desc, shortcut)
        self.module = module
        self.view_wr = weakref.ref(view)
        self.object_wr = weakref.ref(object)

    def run( self ):
        view = self.view_wr()
        object = self.object_wr()
        if not view or not object:
            return
        handle = self.module.run_object_command(self.id, object)
        if handle:
            view.open(handle)


class Module(object):

    module_registry = []

    def __init__( self ):
        self.module_registry.append(self)

    def get_object_commands( self, object ):
        return []

    def run_object_command( self, command_id, object ):
        assert False, repr(command_id)  # Unknown command

    @classmethod
    def get_all_object_commands( cls, view, object ):
        commands = []
        for module in cls.module_registry:
            commands += [ModuleCommand.from_command(cmd, module, view, object)
                         for cmd in module.get_object_commands(object)]
        return commands
