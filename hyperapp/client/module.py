import asyncio
import weakref
from .command_class import Commander, Command


class Module(Commander):

    module_registry = []  # todo: remove global, make separate registry

    def __init__( self, services ):
        Commander.__init__(self, commands_kind='global')
        self.module_registry.append(self)

    def get_object_commands( self, object ):
        return []

    @classmethod
    def get_all_commands( cls ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_commands()
        return commands

    @classmethod
    def get_all_object_commands( cls, object ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_object_commands(object)
        return [cmd.clone(args=(object,)) for cmd in commands]
