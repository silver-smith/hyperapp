
class Module(object):

    module_registry = []

    def __init__( self ):
        self.module_registry.append(self)

    def get_object_commands( self, object ):
        return []

    def run_object_command( self, command_id ):
        assert False, repr(command_id)  # Unknown command

    @classmethod
    def get_all_object_commands( cls, object ):
        commands = []
        for module in cls.module_registry:
            commands += [cmd.as_object_command(module) for cmd in module.get_object_commands(object)]
        return commands
