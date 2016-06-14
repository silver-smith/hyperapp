import asyncio
import weakref
from .command import RunnableCommand


class ModuleCommand(RunnableCommand):

    @classmethod
    def from_command( cls, cmd, module, view ):
        return cls(cmd.id, cmd.text, cmd.desc, cmd.shortcut, module, view)

    def __init__( self, id, text, desc, shortcut, module, view ):
        RunnableCommand.__init__(self, id, text, desc, shortcut)
        self.module = module
        self.view_wr = weakref.ref(view)

    @asyncio.coroutine
    def run( self ):
        view = self.view_wr()
        if not view:
            return
        handle = yield from self.module.run_command(self.id)
        if handle:
            view.open(handle)


class ObjectModuleCommand(RunnableCommand):

    @classmethod
    def from_command( cls, cmd, module, view, object ):
        return cls(cmd.id, cmd.text, cmd.desc, cmd.shortcut, module, view, object)

    def __init__( self, id, text, desc, shortcut, module, view, object ):
        RunnableCommand.__init__(self, id, text, desc, shortcut)
        self.module = module
        self.view_wr = weakref.ref(view)
        self.object_wr = weakref.ref(object)

    @asyncio.coroutine
    def run( self ):
        view = self.view_wr()
        object = self.object_wr()
        if not view or not object:
            return
        handle = yield from self.module.run_object_command(self.id, object)
        if handle:
            view.open(handle)


class Module(object):

    module_registry = []

    def __init__( self ):
        self.module_registry.append(self)

    def get_commands( self ):
        return []

    def get_object_commands( self, object ):
        return []

    @asyncio.coroutine
    def run_command( self, command_id, initiator_view ):
        assert False, repr(command_id)  # Unknown command

    def run_object_command( self, command_id, object, initiator_view ):
        assert False, repr(command_id)  # Unknown command

    @classmethod
    def get_all_commands( cls, view ):
        commands = []
        for module in cls.module_registry:
            commands += [ModuleCommand.from_command(cmd, module, view) for cmd in module.get_commands()]
        return commands

    @classmethod
    def get_all_object_commands( cls, view, object ):
        commands = []
        for module in cls.module_registry:
            commands += [ObjectModuleCommand.from_command(cmd, module, view, object)
                         for cmd in module.get_object_commands(object)]
        return commands
